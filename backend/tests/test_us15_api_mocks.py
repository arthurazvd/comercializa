"""Testes automatizados de API e integração com Mock Objects para a US15.

Cobre a especificação da Iteração 1:
- Testes unitários utilizando Mock Objects (unittest.mock) para isolar serviços e ORM;
- Testes de integração funcionais via APIClient validando persistência, códigos HTTP e integridade referencial.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from django.db.models.deletion import ProtectedError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory

from core.models import Category, Product, Sale, SaleItem
from core.serializers import ProductSerializer
from core.views import DashboardView, ProductViewSet


# ==============================================================================
# 1. TESTES UNITÁRIOS COM MOCK OBJECTS (Isolamento de dependências externas)
# ==============================================================================

def test_dashboard_view_isolated_with_mock_object():
    """Valida o endpoint de dashboard isolando o serviço analítico via Mock Object."""
    mock_payload = {
        "gross_revenue": "1500.00",
        "net_revenue": "1350.00",
        "sales_count": 12,
        "recommendations": [
            {"type": "reposição", "priority": "alta", "product": "Café", "reason": "Estoque mínimo atingido"}
        ],
    }

    factory = APIRequestFactory()
    request = factory.get("/api/dashboard/")

    with patch("core.views.dashboard_data", return_value=mock_payload) as mock_service:
        view = DashboardView.as_view()
        response = view(request)

        assert mock_service.called
        assert response.status_code == status.HTTP_200_OK
        assert response.data == mock_payload


def test_product_viewset_delete_catches_protected_error_with_mock():
    """Valida o tratamento de ProtectedError na exclusão de produto usando Mock Object."""
    factory = APIRequestFactory()
    request = factory.delete("/api/products/1/")

    view = ProductViewSet.as_view({"delete": "destroy"})
    mock_product = MagicMock()
    mock_product.delete.side_effect = ProtectedError("Cannot delete", Product.objects.none())

    with patch.object(ProductViewSet, "get_object", return_value=mock_product):
        response = view(request, pk="1")
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "Este produto possui histórico de vendas ou estoque" in response.data.get("detail", "")


def test_product_serializer_to_representation_with_mock():
    """Valida o serializador de produto com mock de atributos calculados."""
    mock_product = MagicMock()
    mock_product.id = 99
    mock_product.name = "Produto Mockado"
    mock_product.description = "Descrição de teste"
    mock_product.category = None
    mock_product.sku = "MOCK-001"
    mock_product.purchase_price = Decimal("10.00")
    mock_product.sale_price = Decimal("20.00")
    mock_product.margin = Decimal("10.00")
    mock_product.stock = 50
    mock_product.minimum_stock = 10
    mock_product.expiration_date = None
    mock_product.perishable = False
    mock_product.active = True
    mock_product.created_at = None
    mock_product.image_updated_at = None
    mock_product._comercializa_snapshot = {
        "available_stock": 50,
        "expired_units": 0,
        "expiring_units": 0,
        "nearest_expiration": None,
    }

    serializer = ProductSerializer(mock_product)
    data = serializer.data

    assert data["name"] == "Produto Mockado"
    assert data["sku"] == "MOCK-001"
    assert str(data["sale_price"]) == "20.00"
    assert str(data["margin"]) == "10.00"
    assert data["available_stock"] == 50


# ==============================================================================
# 2. TESTES DE INTEGRAÇÃO FUNCIONAL VIA APICLIENT (Persistência e Códigos HTTP)
# ==============================================================================

@pytest.mark.django_db
class TestProductAndCategoryAPIIntegration:
    def setup_method(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Higiene e Limpeza")
        self.products_url = reverse("product-list")
        self.categories_url = reverse("category-list")

    def test_create_product_valid_payload_persists_in_db(self):
        """POST /api/products/ persiste o registro e retorna HTTP 201 Created."""
        payload = {
            "name": "Sabonete Líquido 500ml",
            "category": self.category.id,
            "sku": "SAB-500",
            "purchase_price": "4.50",
            "sale_price": "8.90",
            "stock": 30,
            "minimum_stock": 5,
            "perishable": False,
        }
        response = self.client.post(self.products_url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["name"] == "Sabonete Líquido 500ml"
        assert data["sku"] == "SAB-500"
        assert data["category_name"] == "Higiene e Limpeza"

        # Confirmação no banco de dados
        created = Product.objects.get(sku="SAB-500")
        assert created.stock == 30
        assert created.sale_price == Decimal("8.90")

    def test_create_product_missing_required_sale_price_returns_400(self):
        """Tentativa de cadastrar produto sem preço de venda retorna HTTP 400 e não persiste."""
        payload = {
            "name": "Detergente Neutro",
            "category": self.category.id,
            "stock": 10,
        }
        response = self.client.post(self.products_url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "sale_price" in response.json()
        assert not Product.objects.filter(name="Detergente Neutro").exists()

    def test_delete_product_with_sale_items_is_blocked(self):
        """DELETE /api/products/{id}/ retorna HTTP 400 se o produto tiver vendas vinculadas."""
        product = Product.objects.create(
            name="Álcool 70%",
            category=self.category,
            sale_price=Decimal("7.00"),
            stock=15,
        )
        sale = Sale.objects.create()
        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=2,
            unit_price=Decimal("7.00"),
        )

        detail_url = reverse("product-detail", kwargs={"pk": product.id})
        response = self.client.delete(detail_url)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "Este produto possui histórico de vendas ou estoque" in response.json()["detail"]
        assert Product.objects.filter(id=product.id).exists()

    def test_update_product_partial_patch_integration(self):
        """PATCH /api/products/{id}/ atualiza apenas os campos enviados e preserva os demais."""
        product = Product.objects.create(
            name="Esponja Multiuso",
            category=self.category,
            purchase_price=Decimal("1.00"),
            sale_price=Decimal("2.50"),
            stock=40,
        )
        detail_url = reverse("product-detail", kwargs={"pk": product.id})
        patch_payload = {"sale_price": "3.00", "stock": 35}

        response = self.client.patch(detail_url, patch_payload, format="json")
        assert response.status_code == status.HTTP_200_OK

        product.refresh_from_db()
        assert product.sale_price == Decimal("3.00")
        assert product.stock == 35
        assert product.name == "Esponja Multiuso"  # Inalterado
