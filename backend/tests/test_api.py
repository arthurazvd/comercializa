import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from core.models import Product, Sale, SaleItem
from tests.factories import CategoryFactory, ProductFactory, SaleFactory, SaleItemFactory


@pytest.mark.django_db
class TestProductAPI:
    """Testes de integração da API de produtos"""

    def setup_method(self):
        self.client = APIClient()

    def test_list_products(self):
        """Listar produtos"""
        ProductFactory.create_batch(3)
        response = self.client.get("/api/products/")
        assert response.status_code == 200
        assert len(response.data) == 3

    def test_create_product_valid(self):
        """CT01: Cadastrar produto válido"""
        category = CategoryFactory()
        payload = {
            "name": "Arroz Integral",
            "category": category.id,
            "sale_price": "12.50",
            "purchase_price": "8.00",
            "stock": 50,
            "minimum_stock": 5,
            "active": True,
        }
        response = self.client.post("/api/products/", payload, format="json")
        assert response.status_code == 201
        assert response.data["name"] == "Arroz Integral"
        assert Product.objects.filter(name="Arroz Integral").exists()

    def test_create_product_missing_required_field(self):
        """Criar produto sem campo obrigatório"""
        payload = {
            "category": CategoryFactory().id,
            # falta 'sale_price'
        }
        response = self.client.post("/api/products/", payload, format="json")
        assert response.status_code == 400

    def test_retrieve_product(self):
        """CT02: Recuperar detalhes de um produto"""
        product = ProductFactory(name="Feijão Carioca")
        response = self.client.get(f"/api/products/{product.id}/")
        assert response.status_code == 200
        assert response.data["name"] == "Feijão Carioca"

    def test_update_product(self):
        """CT02: Editar produto"""
        product = ProductFactory(name="Produto Antigo", stock=10)
        payload = {
            "name": "Produto Novo",
            "stock": 20,
            "sale_price": product.sale_price,
            "purchase_price": product.purchase_price,
        }
        response = self.client.patch(f"/api/products/{product.id}/", payload, format="json")
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.name == "Produto Novo"
        assert product.stock == 20

    def test_delete_product_without_sales(self):
        """CT03: Excluir produto sem dependência"""
        product = ProductFactory()
        product_id = product.id
        response = self.client.delete(f"/api/products/{product_id}/")
        assert response.status_code == 204
        assert not Product.objects.filter(id=product_id).exists()

    def test_delete_product_with_sales_fails(self):
        """Excluir produto com vendas deve falhar"""
        product = ProductFactory()
        sale = SaleFactory()
        SaleItemFactory(sale=sale, product=product)

        # Tentar deletar - vai gerar erro ou retornar status de erro
        try:
            response = self.client.delete(f"/api/products/{product.id}/")
            # Se chegar aqui, não foi 204 (sucesso)
            assert response.status_code != 204
        except Exception:
            # Se lançar exceção, é porque está protegido
            pass

        # Produto ainda deve existir no banco
        assert Product.objects.filter(id=product.id).exists()

    def test_product_margin_in_response(self):
        """Verificar se margem é retornada na resposta"""
        product = ProductFactory(
            sale_price=Decimal("15.00"),
            purchase_price=Decimal("10.00")
        )
        response = self.client.get(f"/api/products/{product.id}/")
        assert response.status_code == 200
        assert response.data["margin"] == "5.00"


@pytest.mark.django_db
class TestSaleAPI:
    """Testes de integração da API de vendas"""

    def setup_method(self):
        self.client = APIClient()
        self.product = ProductFactory(stock=100, sale_price=Decimal("10.00"))

    def test_list_sales(self):
        """Listar vendas"""
        SaleFactory.create_batch(3)
        response = self.client.get("/api/sales/")
        assert response.status_code == 200
        assert len(response.data) == 3

    def test_create_sale_valid(self):
        """CT04: Registrar venda com estoque"""
        payload = {
            "discount": "0.00",
            "items": [
                {"product": self.product.id, "quantity": 5}
            ]
        }
        response = self.client.post("/api/sales/", payload, format="json")
        assert response.status_code == 201
        assert response.data["total"] == "50.00"

    def test_sale_reduces_stock(self):
        """CT04: Venda salva e estoque reduzido"""
        initial_stock = self.product.stock
        payload = {
            "discount": "0.00",
            "items": [
                {"product": self.product.id, "quantity": 10}
            ]
        }
        response = self.client.post("/api/sales/", payload, format="json")
        assert response.status_code == 201
        self.product.refresh_from_db()
        assert self.product.stock == initial_stock - 10

    def test_sale_multiple_items(self):
        """Venda com múltiplos itens"""
        product2 = ProductFactory(stock=50, sale_price=Decimal("20.00"))
        payload = {
            "discount": "0.00",
            "items": [
                {"product": self.product.id, "quantity": 5},
                {"product": product2.id, "quantity": 3}
            ]
        }
        response = self.client.post("/api/sales/", payload, format="json")
        assert response.status_code == 201
        assert len(response.data["items"]) == 2
        assert response.data["total"] == "110.00"  # 50 + 60

    def test_sale_with_discount(self):
        """Venda com desconto"""
        payload = {
            "discount": "5.00",
            "items": [
                {"product": self.product.id, "quantity": 10}
            ]
        }
        response = self.client.post("/api/sales/", payload, format="json")
        assert response.status_code == 201
        assert response.data["total"] == "95.00"  # 100 - 5

    def test_sale_rejects_insufficient_stock(self):
        """CT05: Vender acima do estoque"""
        payload = {
            "discount": "0.00",
            "items": [
                {"product": self.product.id, "quantity": 999}
            ]
        }
        response = self.client.post("/api/sales/", payload, format="json")
        assert response.status_code == 400
        self.product.refresh_from_db()
        assert self.product.stock == 100  # estoque não alterado

    def test_sale_duplicate_product_error(self):
        """Erro ao informar mesmo produto duas vezes"""
        payload = {
            "discount": "0.00",
            "items": [
                {"product": self.product.id, "quantity": 5},
                {"product": self.product.id, "quantity": 3}
            ]
        }
        response = self.client.post("/api/sales/", payload, format="json")
        assert response.status_code == 400

    def test_sale_empty_items_error(self):
        """Venda sem itens deve falhar"""
        payload = {
            "discount": "0.00",
            "items": []
        }
        response = self.client.post("/api/sales/", payload, format="json")
        assert response.status_code == 400

    def test_sale_items_in_list(self):
        """Vendas listadas incluem seus itens"""
        sale = SaleFactory()
        SaleItemFactory(sale=sale, product=self.product, quantity=2)
        response = self.client.get("/api/sales/")
        assert response.status_code == 200
        # Ao menos uma venda deve ter itens
        sales_with_items = [s for s in response.data if len(s["items"]) > 0]
        assert len(sales_with_items) >= 1


@pytest.mark.django_db
class TestCategoryAPI:
    """Testes de integração da API de categorias"""

    def setup_method(self):
        self.client = APIClient()

    def test_list_categories(self):
        """Listar categorias"""
        CategoryFactory.create_batch(3)
        response = self.client.get("/api/categories/")
        assert response.status_code == 200
        assert len(response.data) == 3

    def test_create_category(self):
        """Criar categoria"""
        payload = {"name": "Alimentos"}
        response = self.client.post("/api/categories/", payload, format="json")
        assert response.status_code == 201
        assert response.data["name"] == "Alimentos"
