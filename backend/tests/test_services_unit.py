from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.utils import timezone

from core.models import Product, StockLot, Sale, SaleItem
from core.services import (
    PRIORITY_MEDIUM,
    _expiration_recommendations,
    _product_recommendations,
    _restock_recommendation,
    calculate_restock_quantity,
    calculate_revenue,
    dashboard_data,
)
from core.stock_lots import stock_snapshot
from tests.factories import ProductFactory


class TesteCalculoFaturamento:
    """Testes unitários da regra de cálculo do faturamento."""

    def teste_receita_sem_desconto(self):
        resultado = calculate_revenue(
            Decimal("100.00"),
            Decimal("0.00"),
        )

        assert resultado == Decimal("100.00")

    def teste_receita_com_desconto(self):
        resultado = calculate_revenue(
            Decimal("100.00"),
            Decimal("25.00"),
        )

        assert resultado == Decimal("75.00")

    def teste_receita_nao_pode_ser_negativa(self):
        resultado = calculate_revenue(
            Decimal("50.00"),
            Decimal("100.00"),
        )

        assert resultado == Decimal("0")

    @pytest.mark.parametrize(
        ("gross_revenue", "discounts", "expected"),
        [
            (Decimal("0.00"), Decimal("0.00"), Decimal("0")),
            (Decimal("100.01"), Decimal("100.01"), Decimal("0")),
            (Decimal("100.01"), Decimal("0.01"), Decimal("100.00")),
            (Decimal("0.01"), Decimal("0.02"), Decimal("0")),
            (Decimal("10.999"), Decimal("0.001"), Decimal("10.998")),
        ],
    )
    def teste_receita_respeita_todas_as_fronteiras(
        self, gross_revenue, discounts, expected
    ):
        assert calculate_revenue(gross_revenue, discounts) == expected

    def teste_receita_preserva_decimal_e_nao_converte_para_float(self):
        resultado = calculate_revenue(Decimal("1.10"), Decimal("0.10"))

        assert isinstance(resultado, Decimal)
        assert resultado == Decimal("1.00")


class TesteCalculoReposicao:
    """Testes unitários da regra de sugestão de reposição."""

    def teste_reposicao_considera_estoque_minimo(self):
        resultado = calculate_restock_quantity(
            stock=5,
            minimum_stock=10,
            velocity=0,
        )

        assert resultado == 15

    def teste_reposicao_considera_velocidade_de_vendas(self):
        resultado = calculate_restock_quantity(
            stock=5,
            minimum_stock=10,
            velocity=2,
        )

        assert resultado == 25

    def teste_reposicao_sugere_pelo_menos_uma_unidade(self):
        resultado = calculate_restock_quantity(
            stock=20,
            minimum_stock=10,
            velocity=0,
        )

        assert resultado == 1

    @pytest.mark.parametrize(
        ("stock", "minimum_stock", "velocity", "expected"),
        [
            (0, 0, 0, 1),
            (10, 10, 0, 10),
            (11, 10, 0, 9),
            (10, 10, 1, 10),
            (5, 10, 0.1, 15),
            (5, 10, 1.5, 17),
        ],
    )
    def teste_reposicao_cobre_fronteiras_e_velocidade_fractional(
        self, stock, minimum_stock, velocity, expected
    ):
        assert calculate_restock_quantity(stock, minimum_stock, velocity) == expected


def _product(name="Produto", stock=10, minimum_stock=5, expiration_date=None):
    return SimpleNamespace(
        id=1,
        name=name,
        stock=stock,
        minimum_stock=minimum_stock,
        expiration_date=expiration_date,
    )


class TesteRecomendacoes:
    def teste_estoque_acima_do_minimo_nao_recomenda_reposicao(self):
        product = _product(stock=10, minimum_stock=5)

        assert _restock_recommendation(product, {"available_stock": 6}, 2) is None

    @pytest.mark.parametrize(
        ("available", "velocity", "priority", "quantity"),
        [
            (0, 0, "alta", 10),
            (1, 1, "alta", 14),
            (4, 1, PRIORITY_MEDIUM, 11),
            (5, 0, PRIORITY_MEDIUM, 5),
        ],
    )
    def teste_reposicao_define_prioridade_e_mensagem(
        self, available, velocity, priority, quantity
    ):
        product = _product(stock=available, minimum_stock=5)

        recommendation = _restock_recommendation(
            product, {"available_stock": available}, velocity
        )

        assert recommendation["priority"] == priority
        assert recommendation["type"] == "reposição"
        assert recommendation["message"] == (
            f"Repor aproximadamente {quantity} unidade(s)."
        )
        assert recommendation["product_id"] == product.id

    def teste_validade_expirada_e_expirando_gera_duas_recomendacoes(self):
        today = date(2026, 11, 4)
        product = _product(stock=3)
        snapshot = {"expired_units": 2, "expiring_units": 1}
        product.lots = SimpleNamespace(
            all=lambda: [
                SimpleNamespace(quantity=1, expiration_date=today + timedelta(days=3))
            ]
        )

        recommendations = _expiration_recommendations(
            product, snapshot, today, today + timedelta(days=15)
        )

        assert [item["type"] for item in recommendations] == ["vencido", "validade"]
        assert recommendations[1]["priority"] == "alta"
        assert "3 dia(s)" in recommendations[1]["reason"]

    @pytest.mark.parametrize(
        ("days", "priority"),
        [(5, "alta"), (6, PRIORITY_MEDIUM), (15, PRIORITY_MEDIUM)],
    )
    def teste_prioridade_de_validade_respeita_limites(
        self, days, priority
    ):
        today = date(2026, 11, 4)
        product = _product(
            stock=1,
            expiration_date=today + timedelta(days=days),
        )
        product.lots = SimpleNamespace(all=lambda: [])

        recommendations = _expiration_recommendations(
            product, {"expired_units": 0, "expiring_units": 1},
            today, today + timedelta(days=15),
        )

        assert len(recommendations) == 1
        assert recommendations[0]["priority"] == priority

    def teste_validade_sem_saldo_nao_recomenda_promocao(self):
        today = date(2026, 11, 4)
        product = _product(stock=0, expiration_date=today + timedelta(days=3))
        product.lots = SimpleNamespace(all=lambda: [])

        assert _expiration_recommendations(
            product, {"expired_units": 0, "expiring_units": 1},
            today, today + timedelta(days=15),
        ) == []

    def teste_baixa_movimentacao_so_aparece_para_produto_nao_vendido(self):
        product = _product(stock=2)
        product.lots = SimpleNamespace(all=lambda: [])
        snapshot = {"available_stock": 2, "expired_units": 0, "expiring_units": 0}

        sold = _product(stock=2)
        sold.id = 2
        sold.lots = product.lots
        assert not any(
            item["type"] == "baixa movimentação"
            for item in _product_recommendations(
                sold, snapshot, 0, {2}, date.today(), date.today()
            )
        )
        assert any(
            item["type"] == "baixa movimentação"
            for item in _product_recommendations(
                product, snapshot, 0, set(), date.today(), date.today()
            )
        )


@pytest.mark.django_db
class TesteSnapshotDeEstoque:
    def teste_snapshot_separa_estoque_legado_lotes_validos_e_vencidos(self):
        today = date(2026, 11, 4)
        product = ProductFactory(
            stock=10, purchase_price=Decimal("3.00"),
            expiration_date=today - timedelta(days=1),
        )
        StockLot.objects.create(
            product=product, quantity=2, received_quantity=2,
            unit_cost=Decimal("5.00"), expiration_date=today + timedelta(days=3),
        )
        StockLot.objects.create(
            product=product, quantity=3, received_quantity=3,
            unit_cost=Decimal("7.00"), expiration_date=today - timedelta(days=2),
        )

        snapshot = stock_snapshot(product, today)

        assert snapshot == {
            "inventory_value": Decimal("46.00"),
            "expired_stock_value": Decimal("36.00"),
            "available_stock": 2,
            "expired_units": 8,
            "expiring_units": 2,
            "nearest_expiration": today - timedelta(days=2),
            "lot_count": 2,
        }

    def teste_snapshot_ignora_lote_vazio_e_calcula_saldo_sem_validade(self):
        today = date(2026, 11, 4)
        product = ProductFactory(
            stock=4, purchase_price=Decimal("2.50"), expiration_date=None
        )
        StockLot.objects.create(
            product=product, quantity=0, received_quantity=2,
            unit_cost=Decimal("9.00"), expiration_date=today - timedelta(days=1),
        )

        snapshot = stock_snapshot(product, today)

        assert snapshot["available_stock"] == 4
        assert snapshot["expired_units"] == 0
        assert snapshot["inventory_value"] == Decimal("10.00")
        assert snapshot["nearest_expiration"] is None
        assert snapshot["lot_count"] == 0


class TesteDashboardComMock:
    """Testa o isolamento de uma regra do serviço usando Mock Object."""

    @patch("core.services.calculate_revenue")
    def teste_dashboard_utiliza_regra_de_calculo_de_receita(
        self,
        mock_calculate_revenue,
        db,
    ):
        mock_calculate_revenue.return_value = Decimal("123.45")

        resultado = dashboard_data()

        # O dashboard usa a função para o consolidado e os sete dias do gráfico.
        assert mock_calculate_revenue.call_count == 8
        mock_calculate_revenue.assert_any_call(Decimal("0"), Decimal("0"))
        assert resultado["summary"]["revenue"] == Decimal("123.45")

    def teste_dashboard_sem_vendas_tem_metricas_zero_e_sete_dias(self, db):
        resultado = dashboard_data()

        assert resultado["summary"]["sales_count"] == 0
        assert resultado["summary"]["revenue"] == Decimal("0")
        assert resultado["summary"]["gross_revenue"] == Decimal("0")
        assert resultado["summary"]["discounts"] == Decimal("0")
        assert resultado["summary"]["average_ticket"] == Decimal("0")
        assert len(resultado["daily_revenue"]) == 7
        assert all(day["revenue"] == Decimal("0") for day in resultado["daily_revenue"])

    def teste_dashboard_exclui_vendas_canceladas_e_produtos_inativos(self, db):
        active = ProductFactory(name="Ativo", stock=4)
        inactive = ProductFactory(name="Inativo", stock=4, active=False)
        sale = Sale.objects.create(discount=Decimal("2.00"))
        SaleItem.objects.create(
            sale=sale, product=active, quantity=2, unit_price=Decimal("10.00")
        )
        canceled = Sale.objects.create(discount=Decimal("0.00"))
        canceled.canceled_at = timezone.now()
        canceled.save(update_fields=["canceled_at"])
        SaleItem.objects.create(
            sale=canceled, product=inactive, quantity=9, unit_price=Decimal("99.00")
        )

        resultado = dashboard_data()

        assert resultado["summary"]["sales_count"] == 1
        assert resultado["summary"]["gross_revenue"] == Decimal("20")
        assert resultado["summary"]["discounts"] == Decimal("2")
        assert resultado["summary"]["revenue"] == Decimal("18")
        assert resultado["summary"]["products_count"] == 1
        assert resultado["top_products"] == [
            {"product_id": active.id, "product__name": "Ativo", "quantity_sold": 2}
        ]
