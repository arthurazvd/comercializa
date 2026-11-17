"""Suíte de testes automatizados de unidade e integração para a US09.

Cobre a classificação de severidade de vencimento, cálculo de risco financeiro,
comportamento de limites temporais e o endpoint REST /api/alerts/expiration/.
"""

from datetime import date, timedelta
from decimal import Decimal
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Category, Product, StockLot
from core.expiration_service import (
    classify_severity,
    get_recommended_action,
    build_alert_payload,
    get_expiration_alerts,
    SEVERITY_EXPIRED,
    SEVERITY_CRITICAL,
    SEVERITY_WARNING,
    SEVERITY_ATTENTION,
)


# ==============================================================================
# 1. TESTES UNITÁRIOS DE CLASSIFICAÇÃO E REGRAS DE DOMÍNIO
# ==============================================================================

@pytest.mark.parametrize(
    "days,window,expected",
    [
        (-10, 30, SEVERITY_EXPIRED),
        (-1, 30, SEVERITY_EXPIRED),
        (0, 30, SEVERITY_CRITICAL),      # Limite inferior de crítico (hoje)
        (3, 30, SEVERITY_CRITICAL),
        (7, 30, SEVERITY_CRITICAL),      # Limite superior de crítico
        (8, 30, SEVERITY_WARNING),       # Limite inferior de alerta
        (12, 30, SEVERITY_WARNING),
        (15, 30, SEVERITY_WARNING),      # Limite superior de alerta
        (16, 30, SEVERITY_ATTENTION),    # Limite inferior de atenção
        (25, 30, SEVERITY_ATTENTION),
        (30, 30, SEVERITY_ATTENTION),    # Limite superior da janela
        (31, 30, None),                  # Fora da janela padrão
        (50, 60, SEVERITY_ATTENTION),    # Dentro de janela expandida
        (61, 60, None),                  # Fora de janela expandida
    ],
)
def test_classify_severity_boundary_values(days, window, expected):
    """Testa a partição de equivalência e valores-limite para classificação de dias."""
    assert classify_severity(days, window) == expected


def test_recommended_action_mappings():
    """Valida se todas as faixas possuem ações recomendadas distintas e fallback."""
    assert "descartar" in get_recommended_action(SEVERITY_EXPIRED).lower()
    assert "liquidação" in get_recommended_action(SEVERITY_CRITICAL).lower()
    assert "desconto" in get_recommended_action(SEVERITY_WARNING).lower()
    assert "priorizar" in get_recommended_action(SEVERITY_ATTENTION).lower()
    assert "monitorar" in get_recommended_action("desconhecido").lower()


@pytest.mark.django_db
def test_build_alert_payload_calculations():
    """Testa o cálculo do capital em risco e receita potencial de um lote."""
    category = Category.objects.create(name="Laticínios")
    product = Product.objects.create(
        name="Queijo Parmesão",
        category=category,
        sku="QUEI-001",
        purchase_price=Decimal("15.00"),
        sale_price=Decimal("25.00"),
        stock=10,
        perishable=True,
    )
    ref_date = date(2026, 11, 1)
    exp_date = date(2026, 11, 4)  # 3 dias -> crítico

    alert = build_alert_payload(
        product=product,
        expiration_date=exp_date,
        quantity=10,
        unit_cost=Decimal("15.00"),
        reference_date=ref_date,
        window_days=30,
        lot_id=1,
    )

    assert alert is not None
    assert alert["product_name"] == "Queijo Parmesão"
    assert alert["category_name"] == "Laticínios"
    assert alert["days_remaining"] == 3
    assert alert["severity"] == SEVERITY_CRITICAL
    assert alert["quantity_at_risk"] == 10
    assert alert["cost_at_risk"] == 150.0  # 10 * 15.00
    assert alert["potential_revenue_loss"] == 250.0  # 10 * 25.00
    assert alert["is_legacy_stock"] is False


@pytest.mark.django_db
def test_build_alert_payload_ignores_zero_quantity_or_out_of_window():
    """Garante que lotes com saldo zero ou além da janela não produzem payload."""
    product = Product.objects.create(
        name="Iogurte",
        sale_price=Decimal("5.00"),
        stock=0,
    )
    ref_date = date(2026, 11, 1)

    # Quantidade zero
    assert build_alert_payload(
        product=product,
        expiration_date=ref_date + timedelta(days=5),
        quantity=0,
        unit_cost=Decimal("2.00"),
        reference_date=ref_date,
        window_days=30,
    ) is None

    # Além da janela
    assert build_alert_payload(
        product=product,
        expiration_date=ref_date + timedelta(days=45),
        quantity=5,
        unit_cost=Decimal("2.00"),
        reference_date=ref_date,
        window_days=30,
    ) is None


# ==============================================================================
# 2. TESTES DE SERVIÇO: get_expiration_alerts COM MÚLTIPLOS LOTES E CENÁRIOS
# ==============================================================================

@pytest.mark.django_db
def test_get_expiration_alerts_aggregates_multiple_lots():
    """Valida o agrupamento de múltiplos lotes em faixas distintas e métricas totais."""
    ref_date = date(2026, 11, 10)
    cat_mercearia = Category.objects.create(name="Mercearia")
    cat_bebidas = Category.objects.create(name="Bebidas")

    p1 = Product.objects.create(
        name="Leite Integral",
        category=cat_bebidas,
        purchase_price=Decimal("4.00"),
        sale_price=Decimal("6.50"),
        stock=30,
        perishable=True,
    )
    # Lote 1: 5 unidades vencidas há 2 dias
    StockLot.objects.create(
        product=p1,
        expiration_date=ref_date - timedelta(days=2),
        quantity=5,
        received_quantity=5,
        unit_cost=Decimal("4.00"),
    )
    # Lote 2: 10 unidades vencendo em 4 dias (crítico)
    StockLot.objects.create(
        product=p1,
        expiration_date=ref_date + timedelta(days=4),
        quantity=10,
        received_quantity=10,
        unit_cost=Decimal("4.20"),
    )
    # Lote 3: 15 unidades vencendo em 20 dias (atenção)
    StockLot.objects.create(
        product=p1,
        expiration_date=ref_date + timedelta(days=20),
        quantity=15,
        received_quantity=15,
        unit_cost=Decimal("4.50"),
    )

    p2 = Product.objects.create(
        name="Biscoito Recheado",
        category=cat_mercearia,
        purchase_price=Decimal("2.00"),
        sale_price=Decimal("3.50"),
        stock=20,
        perishable=True,
    )
    # Lote 4: 20 unidades vencendo em 10 dias (alerta)
    StockLot.objects.create(
        product=p2,
        expiration_date=ref_date + timedelta(days=10),
        quantity=20,
        received_quantity=20,
        unit_cost=Decimal("2.00"),
    )

    # Executa o serviço de alertas
    report = get_expiration_alerts(reference_date=ref_date, window_days=30)

    summary = report["summary"]
    assert summary["total_alerts"] == 4
    assert summary["total_items_at_risk"] == 50  # 5 + 10 + 15 + 20
    assert summary["counts_by_severity"][SEVERITY_EXPIRED] == 1
    assert summary["counts_by_severity"][SEVERITY_CRITICAL] == 1
    assert summary["counts_by_severity"][SEVERITY_WARNING] == 1
    assert summary["counts_by_severity"][SEVERITY_ATTENTION] == 1

    # Custo em risco: (5 * 4.0) + (10 * 4.20) + (15 * 4.50) + (20 * 2.0) = 20 + 42 + 67.5 + 40 = 169.50
    assert summary["total_cost_at_risk"] == 169.50

    # Ordenação: o primeiro alerta da lista deve ser o vencido (menor days_remaining)
    assert report["alerts"][0]["severity"] == SEVERITY_EXPIRED
    assert report["alerts"][0]["days_remaining"] == -2


@pytest.mark.django_db
def test_get_expiration_alerts_legacy_stock_and_filters():
    """Valida tratamento de estoque legado e filtros por severidade e categoria."""
    ref_date = date(2026, 11, 10)
    cat = Category.objects.create(name="Doces")
    p = Product.objects.create(
        name="Geleia de Morango",
        category=cat,
        purchase_price=Decimal("8.00"),
        sale_price=Decimal("14.00"),
        stock=8,
        expiration_date=ref_date + timedelta(days=5),  # Legado sem StockLot
        perishable=True,
    )

    # Filtro por severidade "critico"
    report_critico = get_expiration_alerts(
        reference_date=ref_date,
        window_days=30,
        severity_filter="critico",
    )
    assert len(report_critico["alerts"]) == 1
    assert report_critico["alerts"][0]["product_id"] == p.id
    assert report_critico["alerts"][0]["is_legacy_stock"] is True
    assert report_critico["alerts"][0]["cost_at_risk"] == 64.0  # 8 * 8.00

    # Filtro por severidade "alerta" não deve encontrar a geleia
    report_alerta = get_expiration_alerts(
        reference_date=ref_date,
        window_days=30,
        severity_filter="alerta",
    )
    assert len(report_alerta["alerts"]) == 0


@pytest.mark.django_db
def test_inactive_and_non_perishable_products_are_ignored():
    """Produtos inativos ou sem validade não devem aparecer nos alertas."""
    ref_date = date(2026, 11, 10)
    Product.objects.create(
        name="Produto Inativo",
        purchase_price=Decimal("10.00"),
        sale_price=Decimal("15.00"),
        stock=10,
        expiration_date=ref_date + timedelta(days=2),
        active=False,
    )
    Product.objects.create(
        name="Prego Galvanizado (Não Perecível)",
        purchase_price=Decimal("0.50"),
        sale_price=Decimal("1.00"),
        stock=500,
        expiration_date=None,
        perishable=False,
        active=True,
    )

    report = get_expiration_alerts(reference_date=ref_date, window_days=30)
    assert report["summary"]["total_alerts"] == 0
    assert len(report["alerts"]) == 0


# ==============================================================================
# 3. TESTES DE INTEGRAÇÃO COM A API REST (/api/alerts/expiration/)
# ==============================================================================

@pytest.mark.django_db
class TestExpirationAlertsAPI:
    def setup_method(self):
        self.client = APIClient()
        self.ref_date = date.today()
        self.category = Category.objects.create(name="Panificação")
        self.product = Product.objects.create(
            name="Pão de Forma Artesanal",
            category=self.category,
            purchase_price=Decimal("5.00"),
            sale_price=Decimal("9.00"),
            stock=12,
            perishable=True,
        )
        StockLot.objects.create(
            product=self.product,
            expiration_date=self.ref_date + timedelta(days=2),
            quantity=12,
            received_quantity=12,
            unit_cost=Decimal("5.00"),
        )
        self.url = reverse("expiration-alerts")

    def test_api_success_default_parameters(self):
        """Requisição GET básica retorna HTTP 200 com resumo e lista de alertas."""
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "summary" in data
        assert "alerts" in data
        assert data["summary"]["total_alerts"] == 1
        assert data["alerts"][0]["product_name"] == "Pão de Forma Artesanal"
        assert data["alerts"][0]["severity"] == SEVERITY_CRITICAL
        assert data["alerts"][0]["cost_at_risk"] == 60.0

    def test_api_filter_by_severity_and_category(self):
        """Filtros combinados de severidade e categoria funcionam via query string."""
        # Filtro com categoria existente
        resp_cat = self.client.get(self.url, {"category_id": self.category.id, "severity": "critico"})
        assert resp_cat.status_code == status.HTTP_200_OK
        assert len(resp_cat.json()["alerts"]) == 1

        # Filtro com categoria inexistente
        resp_none = self.client.get(self.url, {"category_id": 9999})
        assert resp_none.status_code == status.HTTP_200_OK
        assert len(resp_none.json()["alerts"]) == 0

    def test_api_validation_error_on_invalid_window_days(self):
        """Parâmetro window_days inválido (não inteiro ou fora do range) retorna HTTP 400."""
        # String não numérica
        r1 = self.client.get(self.url, {"window_days": "invalido"})
        assert r1.status_code == status.HTTP_400_BAD_REQUEST

        # Zero ou negativo
        r2 = self.client.get(self.url, {"window_days": "0"})
        assert r2.status_code == status.HTTP_400_BAD_REQUEST

        # Acima do limite (366)
        r3 = self.client.get(self.url, {"window_days": "400"})
        assert r3.status_code == status.HTTP_400_BAD_REQUEST

    def test_api_validation_error_on_invalid_severity(self):
        """Severidade não reconhecida retorna HTTP 400 com detalhe dos valores aceitos."""
        response = self.client.get(self.url, {"severity": "urgencia_maxima"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Severidade inválida" in response.json()["detail"]

    def test_api_validation_error_on_invalid_category_id(self):
        """category_id não numérico retorna HTTP 400."""
        response = self.client.get(self.url, {"category_id": "abc"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
