import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from core.models import Product, Sale, SaleItem
from tests.factories import CategoryFactory, ProductFactory, SaleFactory, SaleItemFactory


@pytest.mark.django_db
class TesteAceitacao:
    """Testes de aceitação - Cenários de negócio completos"""

    def setup_method(self):
        self.client = APIClient()

    def teste_sem_estoque_negativo_venda(self):
        """Critério de aceitação: nenhuma venda pode gerar estoque negativo"""
        product = ProductFactory(stock=10)

        # Tentar vender mais do que existe
        payload = {
            "discount": "0.00",
            "items": [{"product": product.id, "quantity": 20}]
        }
        response = self.client.post("/api/sales/", payload, format="json")

        # Deve falhar
        assert response.status_code == 400

        # Estoque deve permanecer igual
        product.refresh_from_db()
        assert product.stock == 10
        assert product.stock >= 0

    def teste_estoque_atualizado_mesma_transacao(self):
        """Critério de aceitação: estoque atualizado na mesma transação da venda"""
        product = ProductFactory(stock=50, sale_price=Decimal("10.00"))
        initial_stock = product.stock

        payload = {
            "discount": "0.00",
            "items": [{"product": product.id, "quantity": 15}]
        }
        response = self.client.post("/api/sales/", payload, format="json")

        assert response.status_code == 201

        # Verificar que foi criada uma SaleItem
        sale_id = response.data["id"]
        sale = Sale.objects.get(id=sale_id)
        assert sale.items.count() == 1

        # Estoque deve estar atualizado
        product.refresh_from_db()
        assert product.stock == initial_stock - 15

        # Verificar integridade: items + stock final = stock inicial
        total_sold = sum(item.quantity for item in sale.items.all())
        assert product.stock + total_sold == initial_stock

    def teste_recomendacoes_com_justificativa(self):
        """Critério de aceitação: recomendações devem possuir justificativa"""
        # Criar cenários que geram recomendações
        ProductFactory(stock=0, minimum_stock=20)  # reposição
        ProductFactory(
            expiration_date=timezone.localdate() + timedelta(days=3),
            stock=10
        )  # validade
        ProductFactory(stock=5)  # baixa movimentação

        response = self.client.get("/api/dashboard/")
        recommendations = response.data["recommendations"]

        for rec in recommendations:
            assert "reason" in rec
            assert isinstance(rec["reason"], str)
            assert len(rec["reason"]) > 0

    def teste_regras_sad_deterministicas(self):
        """Critério de aceitação: regras SAD produzem resultados determinísticos"""
        # Criar estado conhecido
        product = ProductFactory(
            name="Teste Determinístico",
            stock=5,
            minimum_stock=10,
            expiration_date=timezone.localdate() + timedelta(days=7)
        )

        # Executar dashboard 3 vezes
        results = []
        for _ in range(3):
            response = self.client.get("/api/dashboard/")
            recs = [r for r in response.data["recommendations"] if r["product_id"] == product.id]
            results.append(recs)

        # Todas as execuções devem ser idênticas
        assert len(results[0]) == len(results[1]) == len(results[2])

        for i in range(len(results[0])):
            assert results[0][i]["type"] == results[1][i]["type"] == results[2][i]["type"]
            assert results[0][i]["priority"] == results[1][i]["priority"] == results[2][i]["priority"]
            assert results[0][i]["reason"] == results[1][i]["reason"] == results[2][i]["reason"]

    def teste_fluxo_create_product_and_sell(self):
        """Fluxo: Criar produto, registrar venda, verificar dashboard"""
        # 1. Criar categoria
        category_payload = {"name": "Alimentos"}
        cat_response = self.client.post("/api/categories/", category_payload, format="json")
        category_id = cat_response.data["id"]

        # 2. Criar produto
        product_payload = {
            "name": "Arroz Premium",
            "category": category_id,
            "sale_price": "15.00",
            "purchase_price": "10.00",
            "stock": 100,
            "minimum_stock": 20,
            "active": True,
        }
        prod_response = self.client.post("/api/products/", product_payload, format="json")
        assert prod_response.status_code == 201
        product_id = prod_response.data["id"]

        # 3. Registrar venda
        sale_payload = {
            "discount": "0.00",
            "items": [{"product": product_id, "quantity": 30}]
        }
        sale_response = self.client.post("/api/sales/", sale_payload, format="json")
        assert sale_response.status_code == 201
        assert sale_response.data["total"] == "450.00"

        # 4. Verificar estoque
        prod_response = self.client.get(f"/api/products/{product_id}/")
        assert prod_response.data["stock"] == 70

        # 5. Verificar dashboard
        dash_response = self.client.get("/api/dashboard/")
        assert dash_response.status_code == 200
        assert dash_response.data["summary"]["sales_count"] == 1
        assert dash_response.data["summary"]["revenue"] == Decimal("450.00")

    def teste_fluxo_low_stock_alert(self):
        """Fluxo: Produto atinge estoque mínimo, gera alerta"""
        product = ProductFactory(
            name="Feijão",
            stock=20,
            minimum_stock=10,
            sale_price=Decimal("8.00")
        )

        # Vender até ficar no mínimo
        payload = {
            "discount": "0.00",
            "items": [{"product": product.id, "quantity": 10}]
        }
        self.client.post("/api/sales/", payload, format="json")

        # Dashboard deve marcar como baixo estoque
        response = self.client.get("/api/dashboard/")
        assert response.data["summary"]["low_stock_count"] == 1

        low_stock_products = [p["name"] for p in response.data["low_stock"]]
        assert "Feijão" in low_stock_products

    def teste_fluxo_expiration_alert(self):
        """Fluxo: Produto próximo ao vencimento, gera alerta"""
        today = timezone.localdate()
        product = ProductFactory(
            name="Iogurte",
            expiration_date=today + timedelta(days=3),
            stock=50
        )

        response = self.client.get("/api/dashboard/")

        # Deve contar como expirando
        assert response.data["summary"]["expiring_count"] == 1

        # Deve ter recomendação de validade
        validade_recs = [r for r in response.data["recommendations"] if r["type"] == "validade"]
        assert len(validade_recs) > 0

    def teste_fluxo_multiple_sales_one_transaction(self):
        """Fluxo: Venda com múltiplos itens em uma transação"""
        product1 = ProductFactory(
            name="Arroz",
            stock=100,
            sale_price=Decimal("10.00")
        )
        product2 = ProductFactory(
            name="Feijão",
            stock=50,
            sale_price=Decimal("12.00")
        )

        payload = {
            "discount": "5.00",
            "items": [
                {"product": product1.id, "quantity": 20},
                {"product": product2.id, "quantity": 15}
            ]
        }
        response = self.client.post("/api/sales/", payload, format="json")

        assert response.status_code == 201
        # Total: (20 * 10) + (15 * 12) - 5 = 200 + 180 - 5 = 375
        assert response.data["total"] == "375.00"

        # Verificar estoque de ambos
        product1.refresh_from_db()
        product2.refresh_from_db()
        assert product1.stock == 80
        assert product2.stock == 35

    def teste_fluxo_inactive_product_not_in_dashboard(self):
        """Fluxo: Produto inativo não aparece no dashboard"""
        active = ProductFactory(active=True, stock=10)
        inactive = ProductFactory(active=False, stock=10)

        response = self.client.get("/api/dashboard/")
        assert response.data["summary"]["products_count"] == 1

    def teste_fluxo_low_velocity_recommendation(self):
        """Fluxo: Produto sem vendas em 30 dias gera recomendação"""
        # Produto vendido
        sold = ProductFactory(name="Vendido", stock=10)
        sale = SaleFactory()
        SaleItemFactory(sale=sale, product=sold, quantity=1)

        # Produto novo (sem vendas)
        new_product = ProductFactory(name="Novo", stock=10)

        response = self.client.get("/api/dashboard/")

        stagnant = [p["name"] for p in response.data["stagnant"]]
        assert "Novo" in stagnant
        assert "Vendido" not in stagnant

    def teste_fluxo_top_products_ranking(self):
        """Fluxo: Ranking de produtos mais vendidos"""
        p1 = ProductFactory(name="Arroz", sale_price=Decimal("10.00"))
        p2 = ProductFactory(name="Feijão", sale_price=Decimal("8.00"))
        p3 = ProductFactory(name="Milho", sale_price=Decimal("5.00"))

        # Arroz: 50 unidades
        sale1 = SaleFactory()
        SaleItemFactory(sale=sale1, product=p1, quantity=50)

        # Feijão: 30 unidades
        sale2 = SaleFactory()
        SaleItemFactory(sale=sale2, product=p2, quantity=30)

        # Milho: 10 unidades
        sale3 = SaleFactory()
        SaleItemFactory(sale=sale3, product=p3, quantity=10)

        response = self.client.get("/api/dashboard/")
        top = response.data["top_products"]

        assert top[0]["product_id"] == p1.id
        assert top[0]["quantity_sold"] == 50
        assert top[1]["product_id"] == p2.id
        assert top[1]["quantity_sold"] == 30
