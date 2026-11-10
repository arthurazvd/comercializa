"""Testes unitários e de API do serviço dashboard (core.services.dashboard_data)."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from core.services import dashboard_data
from tests.factories import ProductFactory, SaleFactory, SaleItemFactory


# Threshold de "expiring" no código de produção (core/reports.py).
# Produtos com validade <= EXPIRING_DAYS são contados como "expiring".
# Ajuste esta constante se o threshold de negócio mudar.
EXPIRING_DAYS = 15


@pytest.fixture
def client():
    return APIClient()


# ---------------------------------------------------------------------------
# Dashboard - summary e listas
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestePainelServico:
    """Testes unitários do serviço dashboard"""

    def teste_painel_empty_state(self):
        data = dashboard_data()
        assert data["period_days"] == 30
        assert data["summary"]["revenue"] == Decimal("0")
        assert data["summary"]["sales_count"] == 0
        assert data["summary"]["products_count"] == 0

    def teste_painel_revenue_calculation(self):
        sale = SaleFactory(discount=Decimal("0"))
        product = ProductFactory(sale_price=Decimal("10.00"))
        SaleItemFactory(sale=sale, product=product, quantity=5,
                        unit_price=Decimal("10.00"))

        data = dashboard_data()
        assert data["summary"]["revenue"] == Decimal("50.00")

    def teste_painel_revenue_with_discount(self):
        sale = SaleFactory(discount=Decimal("10.00"))
        product = ProductFactory()
        SaleItemFactory(sale=sale, product=product,
                        quantity=10, unit_price=Decimal("10.00"))

        data = dashboard_data()
        assert data["summary"]["revenue"] == Decimal("90.00")

    def teste_painel_old_sales_excluded(self):
        old_date = timezone.now() - timedelta(days=40)
        sale = SaleFactory()
        sale.created_at = old_date
        sale.save()
        product = ProductFactory()
        SaleItemFactory(sale=sale, product=product,
                        quantity=10, unit_price=Decimal("10.00"))

        data = dashboard_data()
        assert data["summary"]["revenue"] == Decimal("0")
        assert data["summary"]["sales_count"] == 0

    def teste_painel_sales_count(self):
        SaleFactory.create_batch(5)
        data = dashboard_data()
        assert data["summary"]["sales_count"] == 5

    def teste_painel_products_count(self):
        ProductFactory.create_batch(3, active=True)
        ProductFactory.create_batch(2, active=False)

        data = dashboard_data()
        assert data["summary"]["products_count"] == 3

    def teste_painel_top_products(self):
        """Top 5 produtos mais vendidos, ordenados por quantidade"""
        product1 = ProductFactory(name="Produto A")
        product2 = ProductFactory(name="Produto B")
        product3 = ProductFactory(name="Produto C")

        sale1 = SaleFactory()
        SaleItemFactory(sale=sale1, product=product1, quantity=10)
        SaleItemFactory(sale=sale1, product=product2, quantity=5)

        sale2 = SaleFactory()
        SaleItemFactory(sale=sale2, product=product1, quantity=8)
        SaleItemFactory(sale=sale2, product=product3, quantity=3)

        data = dashboard_data()
        top = data["top_products"]

        # Ordem esperada: product1 (18) > product2 (5) > product3 (3)
        assert top[0]["product_id"] == product1.id
        assert top[0]["quantity_sold"] == 18
        assert top[1]["product_id"] == product2.id
        assert top[1]["quantity_sold"] == 5
        assert top[2]["product_id"] == product3.id
        assert top[2]["quantity_sold"] == 3

    def teste_painel_low_stock_count(self):
        """CT06: Produto atinge estoque mínimo"""
        ProductFactory(stock=5, minimum_stock=10, active=True)
        ProductFactory(stock=20, minimum_stock=10, active=True)
        ProductFactory(stock=10, minimum_stock=10,
                       active=True)  # no limite conta

        data = dashboard_data()
        assert data["summary"]["low_stock_count"] == 2

    def teste_painel_low_stock_list(self):
        ProductFactory(stock=2, minimum_stock=10, name="Produto Crítico")
        ProductFactory(stock=20, minimum_stock=10)

        data = dashboard_data()
        low_stock_products = [p["name"] for p in data["low_stock"]]
        assert "Produto Crítico" in low_stock_products

    def teste_painel_expiring_products(self):
        """
        CT07: Produtos com validade próxima entram em 'expiring'.

        O threshold do projeto é EXPIRING_DAYS (15 dias). Portanto:
          - vence em 3 dias  -> expiring  ✅
          - já vencido       -> NÃO é expiring (é expired)  ❌
          - vence em 30 dias -> NÃO é expiring  ❌
        """
        today = timezone.localdate()
        ProductFactory(
            name="Vence em 3 dias",
            expiration_date=today + timedelta(days=3),
            stock=5,
            active=True,
        )
        ProductFactory(
            name="Já vencido",
            expiration_date=today - timedelta(days=1),
            active=True,
        )
        ProductFactory(
            name="Vence longe",
            expiration_date=today + timedelta(days=30),
            active=True,
        )

        data = dashboard_data()
        expiring_names = [p["name"] for p in data["expiring"]]

        assert data["summary"]["expiring_count"] == 1
        assert "Vence em 3 dias" in expiring_names
        assert "Já vencido" not in expiring_names
        assert "Vence longe" not in expiring_names

    def teste_painel_expiring_threshold_boundary(self):
        """
        Documenta o threshold EXPIRING_DAYS:
          - exatamente no threshold -> expiring
          - um dia além do threshold -> NÃO expiring
        """
        today = timezone.localdate()
        ProductFactory(
            name="No limite",
            expiration_date=today + timedelta(days=EXPIRING_DAYS),
            stock=5,
            active=True,
        )
        ProductFactory(
            name="Um dia além",
            expiration_date=today + timedelta(days=EXPIRING_DAYS + 1),
            stock=5,
            active=True,
        )

        data = dashboard_data()
        expiring_names = [p["name"] for p in data["expiring"]]
        assert "No limite" in expiring_names
        assert "Um dia além" not in expiring_names

    def teste_painel_stagnant_products(self):
        """CT08: Produto sem venda em 30 dias"""
        sold_product = ProductFactory(stock=10)
        sale = SaleFactory()
        SaleItemFactory(sale=sale, product=sold_product, quantity=1)

        ProductFactory(stock=10, name="Parado")

        data = dashboard_data()
        stagnant_names = [p["name"] for p in data["stagnant"]]
        assert "Parado" in stagnant_names

    def teste_painel_stagnant_excludes_zero_stock(self):
        ProductFactory(stock=0)
        ProductFactory(stock=5, name="Com estoque")

        data = dashboard_data()
        stagnant_names = [p["name"] for p in data["stagnant"]]
        assert "Com estoque" in stagnant_names
        assert len(stagnant_names) == 1


# ---------------------------------------------------------------------------
# SAD - recomendações
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TesteRecomendacoesSAD:
    """Testes do Sistema de Apoio à Decisão (SAD)"""

    def teste_recomendacao_reposition_critical_stock(self):
        """CT09: Produto com estoque crítico recomenda reposição"""
        product = ProductFactory(stock=0, minimum_stock=20, name="Arroz")

        data = dashboard_data()
        reposicao = [
            r for r in data["recommendations"]
            if r["type"] == "reposição" and r["product_id"] == product.id
        ]
        assert len(reposicao) > 0
        assert reposicao[0]["priority"] == "alta"
        assert "reason" in reposicao[0]

    def teste_recomendacao_reposition_low_stock(self):
        product = ProductFactory(stock=5, minimum_stock=10, name="Feijão")

        data = dashboard_data()
        reposicao = [
            r for r in data["recommendations"]
            if r["type"] == "reposição" and r["product_id"] == product.id
        ]
        assert len(reposicao) > 0
        assert "suggested_qty" not in reposicao[0]
        assert reposicao[0]["reason"] == "Estoque atual está no nível mínimo ou abaixo dele."

    def teste_recomendacao_expiration_alert(self):
        """CT07: Alerta de validade gera recomendação"""
        today = timezone.localdate()
        product = ProductFactory(
            expiration_date=today + timedelta(days=3),
            stock=10,
            name="Leite",
        )

        data = dashboard_data()
        validade = [
            r for r in data["recommendations"]
            if r["type"] == "validade" and r["product_id"] == product.id
        ]
        assert len(validade) > 0
        assert validade[0]["priority"] == "alta"
        assert "3 dia" in validade[0]["reason"]

    def teste_recomendacao_expiration_medium_priority(self):
        """Alerta de validade com prioridade média (>5 dias, <=EXPIRING_DAYS)"""
        today = timezone.localdate()
        # Usamos 10 dias: > 5 (não é alta) e <= 15 (ainda é expiring).
        product = ProductFactory(
            expiration_date=today + timedelta(days=10),
            stock=10,
        )

        data = dashboard_data()
        validade = [
            r for r in data["recommendations"]
            if r["type"] == "validade" and r["product_id"] == product.id
        ]
        assert len(validade) > 0
        assert validade[0]["priority"] == "média"

    def teste_recomendacao_low_velocity(self):
        """CT08: Baixa movimentação gera recomendação"""
        product = ProductFactory(stock=10, name="Produto Parado")

        data = dashboard_data()
        baixa_mov = [
            r for r in data["recommendations"]
            if r["type"] == "baixa movimentação" and r["product_id"] == product.id
        ]
        assert len(baixa_mov) > 0
        assert baixa_mov[0]["priority"] == "baixa"
        assert "30 dias" in baixa_mov[0]["reason"]

    def teste_recomendacao_has_justification(self):
        ProductFactory(stock=0, minimum_stock=20)
        data = dashboard_data()
        for rec in data["recommendations"]:
            assert "reason" in rec
            assert len(rec["reason"]) > 0

    def teste_recommendations_deterministic(self):
        """Critério: regras do SAD devem produzir resultados determinísticos"""
        product = ProductFactory(
            name="Teste",
            stock=5,
            minimum_stock=10,
            expiration_date=timezone.localdate() + timedelta(days=7),
        )

        data1 = dashboard_data()
        data2 = dashboard_data()

        recs1 = sorted(
            [r for r in data1["recommendations"] if r["product_id"] == product.id],
            key=lambda x: x["type"],
        )
        recs2 = sorted(
            [r for r in data2["recommendations"] if r["product_id"] == product.id],
            key=lambda x: x["type"],
        )

        assert len(recs1) == len(recs2)
        for r1, r2 in zip(recs1, recs2):
            assert r1["type"] == r2["type"]
            assert r1["priority"] == r2["priority"]
            assert r1["reason"] == r2["reason"]

    def teste_recommendations_priority_order(self):
        """Recomendações ordenadas por prioridade (alta > média > baixa)"""
        ProductFactory(
            stock=0, minimum_stock=20)                          # alta
        ProductFactory(                                                    # média
            expiration_date=timezone.localdate() + timedelta(days=7),
            stock=10,
        )
        # baixa
        ProductFactory(stock=5)

        data = dashboard_data()
        priorities = [r["priority"] for r in data["recommendations"]]

        priority_order = {"alta": 0, "média": 1, "baixa": 2}
        for i in range(len(priorities) - 1):
            assert priority_order[priorities[i]
                                  ] <= priority_order[priorities[i + 1]]

    def teste_recommendations_limit(self):
        for _ in range(50):
            ProductFactory(stock=0, minimum_stock=20)

        data = dashboard_data()
        assert len(data["recommendations"]) <= 20


# ---------------------------------------------------------------------------
# API do dashboard
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TesteAPIPainel:
    """Testes da API do dashboard"""

    def teste_painel_endpoint(self, client):
        response = client.get("/api/dashboard/")
        assert response.status_code == 200

    def teste_painel_response_structure(self, client):
        response = client.get("/api/dashboard/")
        assert response.status_code == 200
        data = response.data

        assert "period_days" in data
        assert "summary" in data
        assert "top_products" in data
        assert "low_stock" in data
        assert "expiring" in data
        assert "stagnant" in data
        assert "recommendations" in data

    def teste_painel_summary_fields(self, client):
        response = client.get("/api/dashboard/")
        summary = response.data["summary"]

        assert "revenue" in summary
        assert "sales_count" in summary
        assert "products_count" in summary
        assert "low_stock_count" in summary
        assert "expiring_count" in summary

    def teste_painel_with_real_data(self, client):
        """CT10: Venda registrada atualiza indicadores"""
        product = ProductFactory(stock=100, sale_price=Decimal("10.00"))

        response1 = client.get("/api/dashboard/")
        before = response1.data["summary"]["sales_count"]

        payload = {
            "discount": "0.00",
            "items": [{"product": product.id, "quantity": 5}],
        }
        r = client.post("/api/sales/", payload, format="json")
        assert r.status_code == 201, r.data

        response2 = client.get("/api/dashboard/")
        after = response2.data["summary"]["sales_count"]
        assert after == before + 1
