"""Validações de entrada e operações transacionais da API."""
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework import serializers

from .models import Category, Product, Sale, SaleItem, StockMovement, StockLot, StockLotAllocation
from .stock_lots import stock_snapshot, consume_lots, seal_legacy_stock


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
    available_stock = serializers.SerializerMethodField()
    expired_units = serializers.SerializerMethodField()
    expiring_units = serializers.SerializerMethodField()
    nearest_expiration = serializers.SerializerMethodField()
    margin = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    has_image = serializers.SerializerMethodField()
    purchase_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False)
    sale_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    stock = serializers.IntegerField(min_value=0, required=False)
    minimum_stock = serializers.IntegerField(min_value=0, required=False)

    class Meta:
        model = Product
        fields = [
            "id", "name", "category", "category_name", "sku",
            "purchase_price", "sale_price", "margin", "stock",
            "minimum_stock", "expiration_date", "perishable", "active", "created_at",
            "available_stock", "expired_units", "expiring_units", "nearest_expiration",
            "has_image", "image_updated_at",
        ]
        read_only_fields = ["created_at", "image_updated_at", "has_image"]

    def get_has_image(self, obj):
        return bool(obj.image_updated_at)

    @staticmethod
    def _snapshot(obj):
        # Uma mesma ficha é serializada com quatro indicadores de lote.
        # Calcular uma só vez evita repetir a varredura (e consultas ao banco).
        if not hasattr(obj, '_comercializa_snapshot'):
            obj._comercializa_snapshot = stock_snapshot(obj)
        return obj._comercializa_snapshot

    def get_available_stock(self, obj):
        return self._snapshot(obj)['available_stock']

    def get_expired_units(self, obj):
        return self._snapshot(obj)['expired_units']

    def get_expiring_units(self, obj):
        return self._snapshot(obj)['expiring_units']

    def get_nearest_expiration(self, obj):
        return self._snapshot(obj)['nearest_expiration']

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Informe o nome do produto.")
        return value

    def validate_sku(self, value):
        return value.strip() or None if value is not None else None

    def validate(self, attrs):
        perishable = attrs.get('perishable', getattr(self.instance, 'perishable', False))
        quantity = attrs.get('stock', getattr(self.instance, 'stock', 0))
        expiry = attrs.get('expiration_date', getattr(self.instance, 'expiration_date', None))
        if perishable and quantity > 0 and not expiry and not (self.instance and self.instance.lots.exists()):
            raise serializers.ValidationError({'expiration_date': 'Informe a validade do saldo inicial de um perecível.'})
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        """Não sobrescreve mudanças concorrentes de estoque e audita os ajustes."""
        current = Product.objects.select_for_update().get(pk=instance.pk)
        if current.stock != instance.stock:
            raise serializers.ValidationError(
                {"stock": "Estoque alterado em outra operação. Recarregue os dados."}
            )

        new_stock = validated_data.get("stock", current.stock)
        if new_stock > current.stock and validated_data.get('perishable', current.perishable):
            raise serializers.ValidationError({'stock': 'Para receber um perecível, use Movimentações e informe a validade do lote.'})
        # CAS (compare-and-swap): protege inclusive PUT/PATCH sem campo stock,
        # sem depender exclusivamente de SELECT FOR UPDATE (inócuo no SQLite).
        # Se custo-base for alterado no cadastro, preservar saldo antigo no
        # lote de abertura em vez de reavaliá-lo retroativamente.
        if 'purchase_price' in validated_data and validated_data['purchase_price'] != current.purchase_price:
            seal_legacy_stock(current)
        updated = Product.objects.filter(pk=instance.pk, stock=current.stock).update(**validated_data)
        if not updated:
            raise serializers.ValidationError(
                {"stock": "Estoque alterado em outra operação. Recarregue os dados."}
            )
        if new_stock < current.stock:
            allocations = consume_lots(current, current.stock - new_stock, sale_only=False)
        else:
            allocations = []
        if new_stock != current.stock:
            movement = StockMovement.objects.create(
                product=current,
                delta=new_stock - current.stock,
                stock_before=current.stock,
                stock_after=new_stock,
                reason=StockMovement.Reason.ADJUSTMENT,
                note="Correção de saldo no cadastro do produto",
            )
            for lot, qty in allocations:
                StockLotAllocation.objects.create(movement=movement, lot=lot, quantity=qty)
        instance.refresh_from_db()
        return instance


class SaleItemReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = SaleItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "subtotal", "cost_total"]


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemReadSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    refunded_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Sale
        fields = ["id", "created_at", "discount", "subtotal", "total", "items",
                  "canceled_at", "cancellation_reason", "canceled_by", "refunded_amount"]


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
            if item["quantity"] > stock_snapshot(product)["available_stock"]:
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
            if item["quantity"] > stock_snapshot(product)["available_stock"]:
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
            # Registre o saldo legado como lote de abertura antes de vender.
            # Isso preserva seu custo inclusive se a venda for estornada depois.
            seal_legacy_stock(product)
            allocations = consume_lots(product, quantity, sale_only=True)
            updated = Product.objects.filter(
                pk=product.pk, active=True, stock=product.stock,
            ).update(stock=F("stock") - quantity)
            if not updated:
                raise serializers.ValidationError({"items": f"Estoque indisponível para '{product.name}'."})
            tracked_qty = sum(qty for _, qty in allocations)
            recorded_cost = sum((lot.unit_cost * qty for lot, qty in allocations), Decimal('0'))
            recorded_cost += (quantity - tracked_qty) * product.purchase_price
            SaleItem.objects.create(
                sale=sale, product=product, quantity=quantity,
                unit_price=product.sale_price, cost_total=recorded_cost,
            )
            movement = StockMovement.objects.create(
                product=product, delta=-quantity, stock_before=product.stock,
                stock_after=product.stock - quantity, reason=StockMovement.Reason.SALE,
                note=f"Venda #{sale.pk}", sale=sale,
            )
            for lot, qty in allocations:
                StockLotAllocation.objects.create(movement=movement, lot=lot, quantity=qty)
        return sale


class StockMovementSerializer(serializers.ModelSerializer):
    lots = serializers.SerializerMethodField()

    def get_lots(self, obj):
        outgoing = [
            {'expiration_date': a.lot.expiration_date, 'unit_cost': a.lot.unit_cost,
             'quantity': a.quantity if obj.reason == StockMovement.Reason.REVERSAL else -a.quantity}
            for a in obj.lot_allocations.select_related('lot').all()
        ]
        incoming = [
            {'expiration_date': lot.expiration_date, 'unit_cost': lot.unit_cost,
             'quantity': lot.received_quantity}
            for lot in obj.received_lots.all()
        ]
        return incoming + outgoing

    product_name = serializers.CharField(source="product.name", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    justification_display = serializers.CharField(source="get_justification_display", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id", "product", "product_name", "delta", "stock_before",
            "stock_after", "reason", "reason_display", "justification", "justification_display", "note", "sale", "created_at", "lots", "unit_cost",
        ]
        read_only_fields = fields


class StockAdjustmentSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    delta = serializers.IntegerField(min_value=-1000000000, max_value=1000000000)
    note = serializers.CharField(max_length=255, allow_blank=False, trim_whitespace=True)
    expiration_date = serializers.DateField(required=False, allow_null=True)
    # Para compra: custo do NOVO lote; produto.purchase_price é só referência.
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'), required=False)
    update_reference_cost = serializers.BooleanField(required=False, default=False)
    new_sale_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'), required=False)
    justification = serializers.ChoiceField(choices=StockMovement.Justification.choices, required=False, default='')

    def validate(self, attrs):
        delta = attrs.get('delta', 0)
        expiry = attrs.get('expiration_date')
        justification = attrs.get('justification', '')
        incoming = (StockMovement.Justification.RECEIPT, StockMovement.Justification.RETURN)
        outgoing = (StockMovement.Justification.DAMAGE, StockMovement.Justification.DISCARD)
        if justification in incoming and delta < 0 or justification in outgoing and delta > 0:
            raise serializers.ValidationError({'justification': 'A justificativa é incompatível com entrada ou saída.'})
        if delta > 0 and attrs['product'].perishable and not expiry:
            raise serializers.ValidationError({'expiration_date': 'Informe a validade do novo lote para este perecível.'})
        if expiry and delta <= 0:
            raise serializers.ValidationError({'expiration_date': 'Validade de lote só é permitida em entradas.'})
        if expiry and expiry < timezone.localdate():
            raise serializers.ValidationError({'expiration_date': 'Não é permitido receber um lote já vencido.'})
        purchase = delta > 0 and justification == StockMovement.Justification.RECEIPT
        if not purchase and any(field in attrs for field in ('unit_cost', 'new_sale_price')):
            raise serializers.ValidationError({'unit_cost': 'Custos e preços de compra só são alterados em Recebimento.'})
        if not purchase and attrs.get('update_reference_cost'):
            raise serializers.ValidationError({'update_reference_cost': 'Ajuste de custo somente em Recebimento.'})
        if purchase:
            current = attrs['product']
            cost = attrs.get('unit_cost', current.purchase_price)
            price = attrs.get('new_sale_price', current.sale_price)
            if price <= cost:
                raise serializers.ValidationError({'new_sale_price': 'Preço de venda deve ser maior que o custo deste recebimento. Informe um novo preço.'})
            attrs['unit_cost'] = cost
        return attrs

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
        is_purchase = delta > 0 and validated_data.get('justification') == StockMovement.Justification.RECEIPT
        if is_purchase:
            # Revalidar os preços após bloquear o produto: outra sessão pode
            # ter alterado o custo ou o preço entre o validate() e o create().
            current_cost = validated_data.get('unit_cost', product.purchase_price)
            current_sale_price = validated_data.get('new_sale_price', product.sale_price)
            if current_sale_price <= current_cost:
                raise serializers.ValidationError({'new_sale_price': 'Preço de venda deve superar o custo da entrada.'})
            validated_data['unit_cost'] = current_cost
        if is_purchase and validated_data.get('update_reference_cost'):
            seal_legacy_stock(product)
        allocations = consume_lots(product, -delta, sale_only=False) if delta < 0 else []
        updates = {'stock': F('stock') + delta}
        if is_purchase and validated_data.get('update_reference_cost'):
            updates['purchase_price'] = validated_data['unit_cost']
        if is_purchase and 'new_sale_price' in validated_data:
            updates['sale_price'] = validated_data['new_sale_price']
        updated = Product.objects.filter(pk=product.pk, stock=product.stock).update(**updates)
        if not updated:
            raise serializers.ValidationError({"delta": "Estoque alterado por outra operação. Tente novamente."})
        movement = StockMovement.objects.create(
            product=product, delta=delta, stock_before=product.stock,
            stock_after=after, reason=StockMovement.Reason.ADJUSTMENT,
            note=validated_data["note"], justification=validated_data.get("justification", ""),
            unit_cost=validated_data.get('unit_cost') if is_purchase else None,
        )

        for lot, qty in allocations:
            StockLotAllocation.objects.create(movement=movement, lot=lot, quantity=qty)
        if delta > 0:
            # Entradas de qualquer produto criam seu próprio lote de custo.
            # Devolução não altera o custo de referência no cadastro.
            StockLot.objects.create(
                product=product, expiration_date=validated_data.get('expiration_date'),
                received_quantity=delta, quantity=delta, receipt_movement=movement,
                unit_cost=validated_data.get('unit_cost', product.purchase_price),
            )
        return movement
