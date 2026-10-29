"""Validações de entrada e operações transacionais da API."""
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework import serializers

from .models import Category, Product, Sale, SaleItem, StockMovement


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Informe o nome da categoria.")
        return value


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    margin = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    purchase_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False)
    sale_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    stock = serializers.IntegerField(min_value=0, required=False)
    minimum_stock = serializers.IntegerField(min_value=0, required=False)

    class Meta:
        model = Product
        fields = [
            "id", "name", "category", "category_name", "sku",
            "purchase_price", "sale_price", "margin", "stock",
            "minimum_stock", "expiration_date", "active", "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Informe o nome do produto.")
        return value

    def validate_sku(self, value):
        return value.strip() or None if value is not None else None

    @transaction.atomic
    def update(self, instance, validated_data):
        """Não sobrescreve mudanças concorrentes de estoque e audita os ajustes."""
        current = Product.objects.select_for_update().get(pk=instance.pk)
        if current.stock != instance.stock:
            raise serializers.ValidationError(
                {"stock": "Estoque alterado em outra operação. Recarregue os dados."}
            )

        new_stock = validated_data.get("stock", current.stock)
        # CAS (compare-and-swap): protege inclusive PUT/PATCH sem campo stock,
        # sem depender exclusivamente de SELECT FOR UPDATE (inócuo no SQLite).
        updated = Product.objects.filter(pk=instance.pk, stock=current.stock).update(**validated_data)
        if not updated:
            raise serializers.ValidationError(
                {"stock": "Estoque alterado em outra operação. Recarregue os dados."}
            )
        if new_stock != current.stock:
            StockMovement.objects.create(
                product=current,
                delta=new_stock - current.stock,
                stock_before=current.stock,
                stock_after=new_stock,
                reason=StockMovement.Reason.ADJUSTMENT,
                note="Correção de saldo no cadastro do produto",
            )
        instance.refresh_from_db()
        return instance


class SaleItemReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = SaleItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "subtotal"]


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemReadSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Sale
        fields = ["id", "created_at", "discount", "subtotal", "total", "items"]


class SaleItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(active=True))
    quantity = serializers.IntegerField(min_value=1)


class SaleCreateSerializer(serializers.Serializer):
    discount = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.00"),
        required=False, default=Decimal("0.00"),
    )
    items = SaleItemWriteSerializer(many=True, allow_empty=False)

    def validate_items(self, items):
        seen = set()
        for item in items:
            product = item["product"]
            if product.pk in seen:
                raise serializers.ValidationError(
                    f"O produto '{product.name}' foi informado mais de uma vez."
                )
            seen.add(product.pk)
            if product.expiration_date and product.expiration_date < timezone.localdate():
                raise serializers.ValidationError(f"Produto vencido: '{product.name}'.")
            if item["quantity"] > product.stock:
                raise serializers.ValidationError(
                    f"Estoque insuficiente para '{product.name}'. Disponível: {product.stock}."
                )
        return items

    def validate(self, attrs):
        subtotal = sum(
            (item["product"].sale_price * item["quantity"] for item in attrs["items"]),
            Decimal("0.00"),
        )
        if attrs["discount"] > subtotal:
            raise serializers.ValidationError({"discount": "Desconto não pode superar o subtotal."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Revalida os dados dentro da transação. O UPDATE condicional é seguro
        # também em SQLite (select_for_update sozinho não garante bloqueio).
        items_data = validated_data["items"]
        products = {}
        for item in sorted(items_data, key=lambda item: item["product"].pk):
            product = Product.objects.select_for_update().get(pk=item["product"].pk)
            if not product.active:
                raise serializers.ValidationError({"items": f"Produto inativo: '{product.name}'."})
            if product.expiration_date and product.expiration_date < timezone.localdate():
                raise serializers.ValidationError({"items": f"Produto vencido: '{product.name}'."})
            if item["quantity"] > product.stock:
                raise serializers.ValidationError({"items": f"Estoque insuficiente para '{product.name}'."})
            products[product.pk] = product

        subtotal = sum(
            (products[item["product"].pk].sale_price * item["quantity"] for item in items_data),
            Decimal("0.00"),
        )
        if validated_data["discount"] > subtotal:
            raise serializers.ValidationError({"discount": "Desconto não pode superar o subtotal."})

        sale = Sale.objects.create(discount=validated_data["discount"])
        for item in items_data:
            product = products[item["product"].pk]
            quantity = item["quantity"]
            updated = Product.objects.filter(
                pk=product.pk, active=True, stock__gte=quantity,
            ).filter(
                Q(expiration_date__isnull=True) | Q(expiration_date__gte=timezone.localdate())
            ).update(stock=F("stock") - quantity)
            if not updated:
                raise serializers.ValidationError({"items": f"Estoque indisponível para '{product.name}'."})
            SaleItem.objects.create(
                sale=sale, product=product, quantity=quantity, unit_price=product.sale_price,
            )
            StockMovement.objects.create(
                product=product, delta=-quantity, stock_before=product.stock,
                stock_after=product.stock - quantity, reason=StockMovement.Reason.SALE,
                note=f"Venda #{sale.pk}", sale=sale,
            )
        return sale


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id", "product", "product_name", "delta", "stock_before",
            "stock_after", "reason", "reason_display", "note", "sale", "created_at",
        ]
        read_only_fields = fields


class StockAdjustmentSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    delta = serializers.IntegerField(min_value=-1000000000, max_value=1000000000)
    note = serializers.CharField(max_length=255, allow_blank=False, trim_whitespace=True)

    def validate_delta(self, value):
        if value == 0:
            raise serializers.ValidationError("A movimentação deve ser diferente de zero.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        product = Product.objects.select_for_update().get(pk=validated_data["product"].pk)
        delta = validated_data["delta"]
        after = product.stock + delta
        if not 0 <= after <= 2147483647:
            raise serializers.ValidationError({"delta": "Estoque resultante inválido."})
        updated = Product.objects.filter(pk=product.pk, stock=product.stock).update(stock=F("stock") + delta)
        if not updated:
            raise serializers.ValidationError({"delta": "Estoque alterado por outra operação. Tente novamente."})
        return StockMovement.objects.create(
            product=product, delta=delta, stock_before=product.stock,
            stock_after=after, reason=StockMovement.Reason.ADJUSTMENT,
            note=validated_data["note"],
        )
