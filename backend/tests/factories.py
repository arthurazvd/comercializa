import factory
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from core.models import Category, Product, Sale, SaleItem


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Categoria {n}")


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Produto {n}")
    category = factory.SubFactory(CategoryFactory)
    sku = factory.Sequence(lambda n: f"SKU-{n:05d}")
    purchase_price = Decimal("10.00")
    sale_price = Decimal("15.00")
    stock = 100
    minimum_stock = 10
    active = True
    expiration_date = None


class SaleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Sale

    discount = Decimal("0.00")


class SaleItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SaleItem

    sale = factory.SubFactory(SaleFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 1
    unit_price = Decimal("15.00")
