import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from core.models import Product, Sale, SaleItem
from core.services import dashboard_data
from tests.factories import CategoryFactory, ProductFactory, SaleFactory, SaleItemFactory


@pytest.mark.django_db
class TestDashboardService:
    """Testes unitários do serviço dashboard"""

    def test_dashboard_empty_state(self):
        """Dashboard com nenhum dado"""
        data = dashboard_data()
        assert data["period_days"] == 30
        assert data["summary"]["revenue"] == Decimal("0")
        assert data["summary"]["sales_count"] == 0
        assert data["summary"]["products_count"] == 0

    def test_dashboard_revenue_calculation(self):
        """Validar cálculo de receita nos últimos 30 dias"""
        sale = SaleFactory(discount=Decimal("0"))
        product = ProductFactory(sale_price=Decimal("10.00"))
        SaleItemFactory(sale=sale, product=product, quantity=5, unit_price=Decimal("10.00"))

        data = dashboard_data()
        assert data["summary"]["revenue"] == Decimal("50.00")

    def test_dashboard_revenue_with_discount(self):
        """Receita deve descontar descontos"""
        sale = SaleFactory(discount=Decimal("10.00"))
        product = ProductFactory()
        SaleItemFactory(sale=sale, product=product, quantity=10, unit_price=Decimal("10.00"))

        data = dashboard_data()
        assert data["summary"]["revenue"] == Decimal("90.00")

    def test_dashboard_old_sales_excluded(self):
        """Vendas antigas (>30 dias) não devem ser contadas"""
        old_date = timezone.now() - timedelta(days=40)
        sale = SaleFactory()
        sale.created_at = old_date
        sale.save()
        product = ProductFactory()
        SaleItemFactory(sale=sale, product=product, quantity=10, unit_price=Decimal("10.00"))

        data = dashboard_data()
        assert data["summary"]["revenue"] == Decimal("0")
        assert data["summary"]["sales_count"] == 0

    def test_dashboard_sales_count(self):
        """Contar vendas dos últimos 30 dias"""
        SaleFactory.create_batch(5)
        data = dashboard_data()
        assert data["summary"]["sales_count"] == 5

    def test_dashboard_products_count(self):
        """Contar produtos ativos"""
        ProductFactory.create_batch(3, active=True)
        ProductFactory.create_batch(2, active=False)

        data = dashboard_data()
        assert data["summary"]["products_count"] == 3

    def test_dashboard_top_products(self):
        """Top 5 produtos mais vendidos"""
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
        top_products = data["top_products"]
        assert top_products[0]["product_id"] == product1.id
        assert top_products[0]["quantity_sold"] == 18
        assert top_products[1]["product_id"] == product2.id
        assert top_products[1]["quantity_sold"] == 5

    def test_dashboard_low_stock_count(self):
        """CT06: Produto atinge estoque mínimo"""
        ProductFactory(stock=5, minimum_stock=10, active=True)
        ProductFactory(stock=20, minimum_stock=10, active=True)
        ProductFactory(stock=10, minimum_stock=10, active=True)  # no limite

        data = dashboard_data()
        assert data["summary"]["low_stock_count"] == 2

    def test_dashboard_low_stock_list(self):
        """Lista produtos com estoque crítico"""
        p1 = ProductFactory(stock=2, minimum_stock=10, name="Produto Crítico")
        ProductFactory(stock=20, minimum_stock=10)

        data = dashboard_data()
        low_stock_products = [p["name"] for p in data["low_stock"]]
        assert "Produto Crítico" in low_stock_products

    def test_dashboard_expiring_products(self):
        """CT07: Produto vence em 3 dias"""
        today = timezone.localdate()
        expiring_soon = ProductFactory(
            name="Vence em 3 dias",
            expiration_date=today + timedelta(days=3),
            stock=5,
            active=True
        )
        already_expired = ProductFactory(
            name="Já vencido",
            expiration_date=today - timedelta(days=1),
            active=True
        )
        far_future = ProductFactory(
            name="Vence longe",
            expiration_date=today + timedelta(days=30),
            active=True
        )

        data = dashboard_data()
        assert data["summary"]["expiring_count"] == 1
        expiring_names = [p["name"] for p in data["expiring"]]
        assert "Vence em 3 dias" in expiring_names
        assert "Já vencido" not in expiring_names
        assert "Vence longe" not in expiring_names

    def test_dashboard_stagnant_products(self):
        """CT08: Produto sem venda em 30 dias"""
        # Produto vendido
        sold_product = ProductFactory(stock=10)
        sale = SaleFactory()
        SaleItemFactory(sale=sale, product=sold_product, quantity=1)

        # Produto não vendido
        stagnant = ProductFactory(stock=10, name="Parado")

        data = dashboard_data()
        stagnant_names = [p["name"] for p in data["stagnant"]]
        assert "Parado" in stagnant_names

    def test_dashboard_stagnant_excludes_zero_stock(self):
        """Produtos sem estoque não aparecem como parados"""
        ProductFactory(stock=0)
        ProductFactory(stock=5, name="Com estoque")

        data = dashboard_data()
        stagnant_names = [p["name"] for p in data["stagnant"]]
        assert "Com estoque" in stagnant_names
        assert len(stagnant_names) == 1


@pytest.mark.django_db
class TestSADRecommendations:
    """Testes do Sistema de Apoio à Decisão (SAD)"""

    def test_recommendation_reposition_critical_stock(self):
        """CT09: Produto com estoque crítico recomenda reposição"""
        product = ProductFactory(
            stock=0,
            minimum_stock=20,
            name="Arroz"
        )

        data = dashboard_data()
        recomendacoes = data["recommendations"]
        reposicao = [r for r in recomendacoes if r["type"] == "reposição" and r["product_id"] == product.id]
        assert len(reposicao) > 0
        assert reposicao[0]["priority"] == "alta"
        assert "reason" in reposicao[0]

    def test_recommendation_reposition_low_stock(self):
        """Recomendação de reposição com estoque baixo"""
        product = ProductFactory(
            stock=5,
            minimum_stock=10,
            name="Feijão"
        )

        data = dashboard_data()
        recomendacoes = data["recommendations"]
        reposicao = [r for r in recomendacoes if r["type"] == "reposição" and r["product_id"] == product.id]
        assert len(reposicao) > 0
        assert "suggested_qty" not in reposicao[0]  # não fica no retorno
        assert reposicao[0]["reason"] == "Estoque atual está no nível mínimo ou abaixo dele."

    def test_recommendation_expiration_alert(self):
        """CT07: Alerta de validade gera recomendação"""
        today = timezone.localdate()
        product = ProductFactory(
            expiration_date=today + timedelta(days=3),
            stock=10,
            name="Leite"
        )

        data = dashboard_data()
        recomendacoes = data["recommendations"]
        validade = [r for r in recomendacoes if r["type"] == "validade" and r["product_id"] == product.id]
        assert len(validade) > 0
        assert validade[0]["priority"] == "alta"
        assert "3 dia" in validade[0]["reason"]

    def test_recommendation_expiration_medium_priority(self):
        """Alerta de validade com prioridade média (>5 dias)"""
        today = timezone.localdate()
        product = ProductFactory(
            expiration_date=today + timedelta(days=10),
            stock=10,
        )

        data = dashboard_data()
        recomendacoes = data["recommendations"]
        validade = [r for r in recomendacoes if r["type"] == "validade" and r["product_id"] == product.id]
        assert len(validade) > 0
        assert validade[0]["priority"] == "média"

    def test_recommendation_low_velocity(self):
        """CT08: Baixa movimentação gera recomendação"""
        product = ProductFactory(stock=10, name="Produto Parado")

        data = dashboard_data()
        recomendacoes = data["recommendations"]
        baixa_mov = [r for r in recomendacoes if r["type"] == "baixa movimentação" and r["product_id"] == product.id]
        assert len(baixa_mov) > 0
        assert baixa_mov[0]["priority"] == "baixa"
        assert "30 dias" in baixa_mov[0]["reason"]

    def test_recommendation_has_justification(self):
        """Critério: recomendações devem possuir justificativa"""
        ProductFactory(stock=0, minimum_stock=20)
        data = dashboard_data()
        for rec in data["recommendations"]:
            assert "reason" in rec
            assert len(rec["reason"]) > 0

    def test_recommendations_deterministic(self):
        """Critério: regras do SAD devem produzir resultados determinísticos"""
        product = ProductFactory(
            name="Teste",
            stock=5,
            minimum_stock=10,
            expiration_date=timezone.localdate() + timedelta(days=7)
        )

        data1 = dashboard_data()
        data2 = dashboard_data()

        recs1 = sorted([r for r in data1["recommendations"] if r["product_id"] == product.id],
                       key=lambda x: x["type"])
        recs2 = sorted([r for r in data2["recommendations"] if r["product_id"] == product.id],
                       key=lambda x: x["type"])

        assert len(recs1) == len(recs2)
        for r1, r2 in zip(recs1, recs2):
            assert r1["type"] == r2["type"]
            assert r1["priority"] == r2["priority"]
            assert r1["reason"] == r2["reason"]

    def test_recommendations_priority_order(self):
        """Recomendações ordenadas por prioridade (alta > média > baixa)"""
        # Alta
        ProductFactory(stock=0, minimum_stock=20)
        # Média
        ProductFactory(
            expiration_date=timezone.localdate() + timedelta(days=7),
            stock=10
        )
        # Baixa
        ProductFactory(stock=5)

        data = dashboard_data()
        recs = data["recommendations"]

        priorities = [r["priority"] for r in recs]
        for i in range(len(priorities) - 1):
            priority_order = {"alta": 0, "média": 1, "baixa": 2}
            assert priority_order[priorities[i]] <= priority_order[priorities[i + 1]]

    def test_recommendations_limit(self):
        """Dashboard retorna no máximo 20 recomendações"""
        for _ in range(50):
            ProductFactory(stock=0, minimum_stock=20)

        data = dashboard_data()
        assert len(data["recommendations"]) <= 20


@pytest.mark.django_db
class TestDashboardAPI:
    """Testes da API do dashboard"""

    def setup_method(self):
        self.client = APIClient()

    def test_dashboard_endpoint(self):
        """Acessar endpoint do dashboard"""
        response = self.client.get("/api/dashboard/")
        assert response.status_code == 200

    def test_dashboard_response_structure(self):
        """Validar estrutura da resposta"""
        response = self.client.get("/api/dashboard/")
        assert response.status_code == 200
        data = response.data

        assert "period_days" in data
        assert "summary" in data
        assert "top_products" in data
        assert "low_stock" in data
        assert "expiring" in data
        assert "stagnant" in data
        assert "recommendations" in data

    def test_dashboard_summary_fields(self):
        """Validar campos do resumo"""
        response = self.client.get("/api/dashboard/")
        summary = response.data["summary"]

        assert "revenue" in summary
        assert "sales_count" in summary
        assert "products_count" in summary
        assert "low_stock_count" in summary
        assert "expiring_count" in summary

    def test_dashboard_with_real_data(self):
        """CT10: Venda registrada atualiza indicadores"""
        product = ProductFactory(stock=100, sale_price=Decimal("10.00"))

        # Antes da venda
        response1 = self.client.get("/api/dashboard/")
        before_sales_count = response1.data["summary"]["sales_count"]

        # Fazer uma venda
        payload = {
            "discount": "0.00",
            "items": [{"product": product.id, "quantity": 5}]
        }
        self.client.post("/api/sales/", payload, format="json")

        # Depois da venda
        response2 = self.client.get("/api/dashboard/")
        after_sales_count = response2.data["summary"]["sales_count"]

        assert after_sales_count == before_sales_count + 1
