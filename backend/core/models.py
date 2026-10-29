from decimal import Decimal
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="products"
    )
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=0)
    expiration_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    @property
    def margin(self):
        if not self.sale_price:
            return Decimal("0")
        return self.sale_price - self.purchase_price

    def __str__(self):
        return self.name


class Sale(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def subtotal(self):
        return sum((item.subtotal for item in self.items.all()), Decimal("0"))

    @property
    def total(self):
        return max(self.subtotal - self.discount, Decimal("0"))

    def __str__(self):
        return f"Venda #{self.pk}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sale_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class StockMovement(models.Model):
    """Trilha de auditoria imutável de vendas e ajustes de estoque."""

    class Reason(models.TextChoices):
        SALE = "sale", "Venda"
        ADJUSTMENT = "adjustment", "Ajuste manual"

    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="stock_movements"
    )
    sale = models.ForeignKey(
        Sale, on_delete=models.PROTECT, related_name="stock_movements",
        null=True, blank=True,
    )
    delta = models.IntegerField()
    stock_before = models.PositiveIntegerField()
    stock_after = models.PositiveIntegerField()
    reason = models.CharField(max_length=20, choices=Reason.choices)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.product}: {self.delta:+d} ({self.get_reason_display()})"
