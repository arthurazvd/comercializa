from django.db import transaction
from rest_framework import serializers
from .models import Category, Product, Sale, SaleItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    margin = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "category", "category_name", "sku",
            "purchase_price", "sale_price", "margin",
            "stock", "minimum_stock", "expiration_date",
            "active", "created_at",
        ]


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
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    items = SaleItemWriteSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("A venda deve possuir ao menos um item.")
        seen = set()
        for item in items:
            product = item["product"]
            if product.id in seen:
                raise serializers.ValidationError(
                    f"O produto '{product.name}' foi informado mais de uma vez."
                )
            seen.add(product.id)
            if item["quantity"] > product.stock:
                raise serializers.ValidationError(
                    f"Estoque insuficiente para '{product.name}'. Disponível: {product.stock}."
                )
        return items

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        sale = Sale.objects.create(**validated_data)

        for item in items_data:
            product = Product.objects.select_for_update().get(pk=item["product"].pk)
            quantity = item["quantity"]

            if quantity > product.stock:
                raise serializers.ValidationError(
                    f"Estoque insuficiente para '{product.name}'."
                )

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=product.sale_price,
            )
            product.stock -= quantity
            product.save(update_fields=["stock"])

        return sale
