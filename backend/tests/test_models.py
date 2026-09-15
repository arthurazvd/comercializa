import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from core.models import Category, Product, Sale, SaleItem
from tests.factories import CategoryFactory, ProductFactory, SaleFactory, SaleItemFactory


@pytest.mark.django_db
class TestProductModel:
    """Testes unitários do modelo Product"""

    def test_create_product_valid(self):
        """CT01: Cadastrar produto válido"""
        category = CategoryFactory()
        product = Product.objects.create(
            name="Arroz",
            category=category,
            sale_price=Decimal("10.00"),
            purchase_price=Decimal("7.00"),
            stock=100,
            minimum_stock=10
        )
        assert product.id is not None
        assert product.name == "Arroz"
        assert product.stock == 100

    def test_product_margin_calculation(self):
        """Validar cálculo de margem"""
        product = ProductFactory(
            sale_price=Decimal("15.00"),
            purchase_price=Decimal("10.00")
        )
        assert product.margin == Decimal("5.00")

    def test_product_margin_zero_sale_price(self):
        """Validar margem com preço de venda zero"""
        product = ProductFactory(
            sale_price=Decimal("0.00"),
            purchase_price=Decimal("10.00")
        )
        assert product.margin == Decimal("0.00")

    def test_product_string_representation(self):
        """Validar representação em string"""
        product = ProductFactory(name="Feijão")
        assert str(product) == "Feijão"

    def test_product_active_by_default(self):
        """Produto deve estar ativo por padrão"""
        product = ProductFactory()
        assert product.active is True

    def test_product_timestamps(self):
        """Validar timestamps de criação"""
        product = ProductFactory()
        assert product.created_at is not None


@pytest.mark.django_db
class TestSaleModel:
    """Testes unitários do modelo Sale"""

    def test_sale_subtotal_calculation(self):
        """Validar cálculo de subtotal"""
        sale = SaleFactory()
        SaleItemFactory(sale=sale, quantity=2, unit_price=Decimal("10.00"))
        SaleItemFactory(sale=sale, quantity=3, unit_price=Decimal("5.00"))

        assert sale.subtotal == Decimal("35.00")

    def test_sale_total_with_discount(self):
        """Validar cálculo de total com desconto"""
        sale = SaleFactory(discount=Decimal("5.00"))
        SaleItemFactory(sale=sale, quantity=1, unit_price=Decimal("20.00"))

        assert sale.total == Decimal("15.00")

    def test_sale_total_no_negative(self):
        """Total não deve ser negativo mesmo com desconto maior"""
        sale = SaleFactory(discount=Decimal("100.00"))
        SaleItemFactory(sale=sale, quantity=1, unit_price=Decimal("10.00"))

        assert sale.total == Decimal("0.00")

    def test_sale_string_representation(self):
        """Validar representação em string"""
        sale = SaleFactory()
        assert str(sale) == f"Venda #{sale.pk}"


@pytest.mark.django_db
class TestSaleItemModel:
    """Testes unitários do modelo SaleItem"""

    def test_sale_item_subtotal(self):
        """Validar cálculo de subtotal do item"""
        item = SaleItemFactory(quantity=5, unit_price=Decimal("12.50"))
        assert item.subtotal == Decimal("62.50")

    def test_sale_item_zero_quantity(self):
        """Item com quantidade zero"""
        item = SaleItemFactory(quantity=0)
        assert item.subtotal == Decimal("0.00")


@pytest.mark.django_db
class TestCategoryModel:
    """Testes unitários do modelo Category"""

    def test_create_category_unique_name(self):
        """Categoria com nome único"""
        CategoryFactory(name="Alimentos")
        with pytest.raises(Exception):  # IntegrityError
            CategoryFactory(name="Alimentos")

    def test_category_string_representation(self):
        """Validar representação em string"""
        category = CategoryFactory(name="Bebidas")
        assert str(category) == "Bebidas"
