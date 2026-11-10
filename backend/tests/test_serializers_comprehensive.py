"""Testes abrangentes para serializers.py - cobre todas as ramificações (happy/sad paths)."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from core.models import (
    Product,
    StockLot,
    StockLotAllocation,
    StockMovement,
)
from core.serializers import (
    CategorySerializer,
    ProductSerializer,
    SaleCreateSerializer,
    SaleItemWriteSerializer,
    StockAdjustmentSerializer,
    StockMovementSerializer,
)
from tests.factories import CategoryFactory, ProductFactory


@pytest.mark.django_db
class TestCategorySerializer:
    """Testes para CategorySerializer (linhas 13-22)"""

    def test_valid_category(self):
        data = {'name': 'Nova Categoria'}
        serializer = CategorySerializer(data=data)
        assert serializer.is_valid()
        category = serializer.save()
        assert category.name == 'Nova Categoria'

    def test_invalid_empty_name(self):
        data = {'name': ''}
        serializer = CategorySerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
        assert 'não estar em branco' in str(serializer.errors['name'])

    def test_invalid_whitespace_name(self):
        data = {'name': '   '}
        serializer = CategorySerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

    def test_name_stripped(self):
        data = {'name': '  Categoria Teste  '}
        serializer = CategorySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['name'] == 'Categoria Teste'

    def test_unique_name_constraint(self):
        CategoryFactory(name='Existente')
        data = {'name': 'Existente'}
        serializer = CategorySerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors


@pytest.mark.django_db
class TestProductSerializer:
    """Testes para ProductSerializer (linhas 25-129)"""

    def test_valid_product(self):
        category = CategoryFactory()
        data = {
            'name': 'Produto Teste',
            'category': category.id,
            'sale_price': '15.00',
            'purchase_price': '10.00',
            'stock': 10,
            'minimum_stock': 5,
        }
        serializer = ProductSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        product = serializer.save()
        assert product.name == 'Produto Teste'

    def test_invalid_empty_name(self):
        category = CategoryFactory()
        data = {
            'name': '',
            'category': category.id,
            'sale_price': '15.00',
        }
        serializer = ProductSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
        assert 'não estar em branco' in str(serializer.errors['name'])

    def test_invalid_sku_whitespace(self):
        category = CategoryFactory()
        data = {
            'name': 'Produto',
            'category': category.id,
            'sale_price': '15.00',
            'sku': '  SKU-001  ',
        }
        serializer = ProductSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['sku'] == 'SKU-001'

    def test_sku_none_allowed(self):
        category = CategoryFactory()
        data = {
            'name': 'Produto',
            'category': category.id,
            'sale_price': '15.00',
            'sku': None,
        }
        serializer = ProductSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['sku'] is None

    def test_perishable_requires_expiration(self):
        category = CategoryFactory()
        data = {
            'name': 'Perecível',
            'category': category.id,
            'sale_price': '15.00',
            'stock': 10,
            'perishable': True,
            'expiration_date': None,
        }
        serializer = ProductSerializer(data=data)
        assert not serializer.is_valid()
        assert 'expiration_date' in serializer.errors
        assert 'validade do saldo inicial' in str(
            serializer.errors['expiration_date'])

    def test_perishable_with_lots_allows_no_expiration(self):
        category = CategoryFactory()
        product = ProductFactory(
            category=category, perishable=True, stock=0)
        StockLot.objects.create(
            product=product, received_quantity=10, quantity=10,
            unit_cost=Decimal('10.00'),
        )

        data = {
            'name': 'Perecível',
            'category': category.id,
            'sale_price': '15.00',
            'stock': 0,
            'perishable': True,
            'expiration_date': None,
        }
        serializer = ProductSerializer(product, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors

    def test_snapshot_cached(self):
        product = ProductFactory()
        serializer = ProductSerializer(product)

        avail1 = serializer.get_available_stock(product)
        avail2 = serializer.get_available_stock(product)
        assert avail1 == avail2
        assert hasattr(product, '_comercializa_snapshot')


@pytest.mark.django_db
class TestProductSerializerUpdate:
    """Testes para ProductSerializer.update (linhas 90-129)"""

    def test_update_concurrent_stock_change_raises(self):
        product = ProductFactory(stock=10)
        serializer = ProductSerializer(
            product, data={'name': 'Novo Nome'}, partial=True)
        assert serializer.is_valid()

        Product.objects.filter(pk=product.pk).update(stock=20)

        with pytest.raises(Exception) as exc:
            serializer.save()
        assert 'Estoque alterado em outra operação' in str(exc.value)

    def test_update_increase_stock_perishable_raises(self):
        product = ProductFactory(
            perishable=True, stock=10,
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        serializer = ProductSerializer(
            product, data={'stock': 20}, partial=True)
        assert serializer.is_valid()

        with pytest.raises(Exception) as exc:
            serializer.save()
        assert 'use Movimentações e informe a validade' in str(exc.value)

    def test_update_purchase_price_change_seals_legacy(self):
        product = ProductFactory(
            stock=10, purchase_price=Decimal('10.00'))
        initial_lots = product.lots.count()

        serializer = ProductSerializer(
            product, data={'purchase_price': '15.00'}, partial=True)
        assert serializer.is_valid()
        serializer.save()

        product.refresh_from_db()
        assert product.lots.count() == initial_lots + 1
        legacy_lot = (
            product.lots
            .filter(receipt_movement__isnull=True)
            .order_by('-id')
            .first()
        )
        assert legacy_lot is not None
        assert legacy_lot.unit_cost == Decimal('10.00')

    def test_update_decrease_stock_consumes_lots(self):
        product = ProductFactory(stock=20)
        StockLot.objects.create(
            product=product, received_quantity=10, quantity=10,
            unit_cost=Decimal('10.00'),
        )

        serializer = ProductSerializer(
            product, data={'stock': 15}, partial=True)
        assert serializer.is_valid()
        serializer.save()

        product.refresh_from_db()
        assert product.stock == 15
        assert StockMovement.objects.filter(
            product=product, reason='adjustment').exists()

    def test_update_increase_stock_non_perishable(self):
        product = ProductFactory(perishable=False, stock=10)
        serializer = ProductSerializer(
            product, data={'stock': 20}, partial=True)
        assert serializer.is_valid()
        serializer.save()

        product.refresh_from_db()
        assert product.stock == 20

    def test_update_cas_fails_on_concurrent_change(self):
        product = ProductFactory(stock=10)
        serializer = ProductSerializer(
            product, data={'stock': 15}, partial=True)
        assert serializer.is_valid()

        Product.objects.filter(pk=product.pk).update(stock=20)

        with pytest.raises(Exception) as exc:
            serializer.save()
        assert 'Estoque alterado em outra operação' in str(exc.value)


@pytest.mark.django_db
class TestSaleCreateSerializer:
    """Testes para SaleCreateSerializer (linhas 158-237)"""

    def test_valid_sale(self):
        product = ProductFactory(
            stock=100, sale_price=Decimal('10.00'))
        data = {
            'discount': '0.00',
            'items': [{'product': product.id, 'quantity': 5}],
        }
        serializer = SaleCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        sale = serializer.save()
        assert sale.items.count() == 1
        assert sale.discount == Decimal('0.00')

    def test_sale_with_discount(self):
        product = ProductFactory(
            stock=100, sale_price=Decimal('10.00'))
        data = {
            'discount': '5.00',
            'items': [{'product': product.id, 'quantity': 5}],
        }
        serializer = SaleCreateSerializer(data=data)
        assert serializer.is_valid()
        sale = serializer.save()
        assert sale.discount == Decimal('5.00')

    def test_sale_invalid_discount_exceeds_subtotal(self):
        product = ProductFactory(
            stock=100, sale_price=Decimal('10.00'))
        data = {
            'discount': '100.00',
            'items': [{'product': product.id, 'quantity': 5}],
        }
        serializer = SaleCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'discount' in serializer.errors
        assert 'não pode superar o subtotal' in str(
            serializer.errors['discount'])

    def test_sale_duplicate_product_error(self):
        product = ProductFactory(
            stock=100, sale_price=Decimal('10.00'))
        data = {
            'discount': '0.00',
            'items': [
                {'product': product.id, 'quantity': 5},
                {'product': product.id, 'quantity': 3},
            ],
        }
        serializer = SaleCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'items' in serializer.errors
        assert 'mais de uma vez' in str(serializer.errors['items'])

    def test_sale_empty_items_error(self):
        data = {'discount': '0.00', 'items': []}
        serializer = SaleCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'items' in serializer.errors

    def test_sale_insufficient_stock(self):
        product = ProductFactory(
            stock=5, sale_price=Decimal('10.00'))
        data = {
            'discount': '0.00',
            'items': [{'product': product.id, 'quantity': 10}],
        }
        serializer = SaleCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'items' in serializer.errors
        assert 'Estoque insuficiente' in str(serializer.errors['items'])

    def test_sale_inactive_product_error(self):
        """Produto inativo é rejeitado pelo queryset (active=True)."""
        product = ProductFactory(
            stock=100, sale_price=Decimal('10.00'), active=False)
        data = {
            'discount': '0.00',
            'items': [{'product': product.id, 'quantity': 5}],
        }
        serializer = SaleCreateSerializer(data=data)
        assert not serializer.is_valid()
        errors_str = str(serializer.errors)
        assert (
            'Produto inativo' in errors_str
            or 'Invalid pk' in errors_str
            or 'does not exist' in errors_str
            or 'Pk inválido' in errors_str
            or 'não existe' in errors_str
        ), errors_str

    def test_sale_concurrent_stock_change_in_create(self):
        product = ProductFactory(
            stock=100, sale_price=Decimal('10.00'))
        data = {
            'discount': '0.00',
            'items': [{'product': product.id, 'quantity': 5}],
        }
        serializer = SaleCreateSerializer(data=data)
        assert serializer.is_valid()

        Product.objects.filter(pk=product.pk).update(stock=50)

        sale = serializer.save()
        assert sale is not None
        product.refresh_from_db()
        assert product.stock == 45

    def test_sale_seals_legacy_stock(self):
        product = ProductFactory(
            stock=10, purchase_price=Decimal('10.00'))
        initial_lots = product.lots.count()

        data = {
            'discount': '0.00',
            'items': [{'product': product.id, 'quantity': 5}],
        }
        serializer = SaleCreateSerializer(data=data)
        assert serializer.is_valid()
        serializer.save()

        product.refresh_from_db()
        assert product.lots.count() == initial_lots + 1

    def test_sale_records_cost_correctly(self):
        product = ProductFactory(
            stock=20, purchase_price=Decimal('10.00'))
        StockLot.objects.create(
            product=product, received_quantity=10, quantity=10,
            unit_cost=Decimal('8.00'),
        )

        data = {
            'discount': '0.00',
            'items': [{'product': product.id, 'quantity': 15}],
        }
        serializer = SaleCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        sale = serializer.save()

        item = sale.items.first()
        assert item.cost_total == Decimal('130.00')


@pytest.mark.django_db
class TestStockAdjustmentSerializer:
    """Testes para StockAdjustmentSerializer (linhas 269-378)"""

    def test_valid_increase_stock(self):
        product = ProductFactory(stock=10)
        data = {
            'product': product.id,
            'delta': 10,
            'note': 'Recebimento',
            'justification': 'recebimento',
        }
        serializer = StockAdjustmentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        movement = serializer.save()
        assert movement.delta == 10
        product.refresh_from_db()
        assert product.stock == 20

    def test_valid_decrease_stock(self):
        product = ProductFactory(stock=20)
        data = {
            'product': product.id,
            'delta': -5,
            'note': 'Avaria',
            'justification': 'avaria',
        }
        serializer = StockAdjustmentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        movement = serializer.save()
        assert movement.delta == -5
        product.refresh_from_db()
        assert product.stock == 15

    def test_zero_delta_invalid(self):
        product = ProductFactory(stock=10)
        data = {'product': product.id, 'delta': 0, 'note': 'Teste'}
        serializer = StockAdjustmentSerializer(data=data)
        assert not serializer.is_valid()
        assert 'delta' in serializer.errors
        assert 'diferente de zero' in str(serializer.errors['delta'])

    def test_invalid_justification_direction_mismatch(self):
        product = ProductFactory(stock=10)

        data = {
            'product': product.id,
            'delta': 10,
            'note': 'Teste',
            'justification': 'avaria',
        }
        serializer = StockAdjustmentSerializer(data=data)
        assert not serializer.is_valid()
        assert 'justification' in serializer.errors
        assert 'incompatível' in str(serializer.errors['justification'])

        data = {
            'product': product.id,
            'delta': -5,
            'note': 'Teste',
            'justification': 'recebimento',
        }
        serializer = StockAdjustmentSerializer(data=data)
        assert not serializer.is_valid()
        assert 'justification' in serializer.errors

    def test_perishable_requires_expiration_on_increase(self):
        product = ProductFactory(perishable=True, stock=10)
        data = {
            'product': product.id,
            'delta': 10,
            'note': 'Recebimento',
            'justification': 'recebimento',
        }
        serializer = StockAdjustmentSerializer(data=data)
        assert not serializer.is_valid()
        assert 'expiration_date' in serializer.errors
        assert 'validade do novo lote' in str(
            serializer.errors['expiration_date'])

    def test_expiration_only_allowed_on_increase(self):
        product = ProductFactory(stock=20)
        data = {
            'product': product.id,
            'delta': -5,
            'note': 'Avaria',
            'justification': 'avaria',
            'expiration_date': date.today() + timedelta(days=30),
        }
        serializer = StockAdjustmentSerializer(data=data)
        assert not serializer.is_valid()
        assert 'expiration_date' in serializer.errors
        assert 'só é permitida em entradas' in str(
            serializer.errors['expiration_date'])

    def test_expired_expiration_date_rejected(self):
        product = ProductFactory(stock=10)
        data = {
            'product': product.id,
            'delta': 10,
            'note': 'Recebimento',
            'justification': 'recebimento',
            'expiration_date': date.today() - timedelta(days=1),
        }
        serializer = StockAdjustmentSerializer(data=data)
        assert not serializer.is_valid()
        assert 'expiration_date' in serializer.errors
        assert 'lote já vencido' in str(
            serializer.errors['expiration_date'])

    def test_purchase_fields_only_on_receipt(self):
        product = ProductFactory(stock=10)
        data = {
            'product': product.id,
            'delta': -5,
            'note': 'Avaria',
            'justification': 'avaria',
            'unit_cost': '10.00',
        }
        serializer = StockAdjustmentSerializer(data=data)
        assert not serializer.is_valid()
        assert 'unit_cost' in serializer.errors
        assert 'só são alterados em Recebimento' in str(
            serializer.errors['unit_cost'])

    def test_purchase_price_validation(self):
        product = ProductFactory(stock=10)
        data = {
            'product': product.id,
            'delta': 10,
            'note': 'Recebimento',
            'justification': 'recebimento',
            'unit_cost': '20.00',
            'new_sale_price': '15.00',
        }
        serializer = StockAdjustmentSerializer(data=data)
        assert not serializer.is_valid()
        assert 'new_sale_price' in serializer.errors
        assert 'deve ser maior que o custo' in str(
            serializer.errors['new_sale_price'])

    def test_purchase_updates_reference_cost(self):
        product = ProductFactory(
            stock=10, purchase_price=Decimal('10.00'))
        data = {
            'product': product.id,
            'delta': 10,
            'note': 'Recebimento',
            'justification': 'recebimento',
            'unit_cost': '12.00',
            'update_reference_cost': True,
        }
        serializer = StockAdjustmentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        product.refresh_from_db()
        assert product.purchase_price == Decimal('12.00')

    def test_concurrent_stock_change_raises(self):
        product = ProductFactory(stock=10)
        data = {
            'product': product.id,
            'delta': 5,
            'note': 'Teste',
        }
        serializer = StockAdjustmentSerializer(data=data)
        assert serializer.is_valid()

        Product.objects.filter(pk=product.pk).update(stock=20)

        movement = serializer.save()
        assert movement is not None
        product.refresh_from_db()
        assert product.stock == 25

    def test_creates_stock_lot_on_receipt(self):
        product = ProductFactory(stock=10)
        data = {
            'product': product.id,
            'delta': 10,
            'note': 'Recebimento',
            'justification': 'recebimento',
            'expiration_date': date.today() + timedelta(days=30),
            'unit_cost': '12.00',
        }
        serializer = StockAdjustmentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        movement = serializer.save()

        lot = StockLot.objects.filter(receipt_movement=movement).first()
        assert lot is not None
        assert lot.quantity == 10
        assert lot.unit_cost == Decimal('12.00')
        assert lot.expiration_date == date.today() + timedelta(days=30)

    def test_consumes_lots_on_decrease(self):
        product = ProductFactory(stock=20)
        StockLot.objects.create(
            product=product, received_quantity=10, quantity=10,
            unit_cost=Decimal('10.00'),
        )

        data = {
            'product': product.id,
            'delta': -5,
            'note': 'Avaria',
            'justification': 'avaria',
        }
        serializer = StockAdjustmentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        product.refresh_from_db()
        assert product.stock == 15
        lot = product.lots.first()
        assert lot.quantity == 5


@pytest.mark.django_db
class TestStockMovementSerializer:
    """Testes para StockMovementSerializer"""

    def test_get_lots_incoming(self):
        product = ProductFactory()
        movement = StockMovement.objects.create(
            product=product, delta=10, stock_before=0, stock_after=10,
            reason='adjustment', justification='recebimento',
        )
        StockLot.objects.create(
            product=product, received_quantity=10, quantity=10,
            unit_cost=Decimal('10.00'), receipt_movement=movement,
        )

        serializer = StockMovementSerializer(movement)
        lots = serializer.get_lots(movement)

        assert len(lots) == 1
        assert lots[0]['quantity'] == 10
        assert lots[0]['unit_cost'] == Decimal('10.00')

    def test_get_lots_outgoing(self):
        product = ProductFactory()
        movement = StockMovement.objects.create(
            product=product, delta=-5, stock_before=10, stock_after=5,
            reason='sale',
        )
        lot = StockLot.objects.create(
            product=product, received_quantity=10, quantity=10,
            unit_cost=Decimal('10.00'),
        )
        StockLotAllocation.objects.create(
            movement=movement, lot=lot, quantity=5,
        )

        serializer = StockMovementSerializer(movement)
        lots = serializer.get_lots(movement)

        assert len(lots) == 1
        assert lots[0]['quantity'] == -5


@pytest.mark.django_db
class TestSaleItemWriteSerializer:
    """Testes para SaleItemWriteSerializer"""

    def test_valid_item(self):
        product = ProductFactory(active=True)
        data = {'product': product.id, 'quantity': 5}
        serializer = SaleItemWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_invalid_quantity_zero(self):
        product = ProductFactory(active=True)
        data = {'product': product.id, 'quantity': 0}
        serializer = SaleItemWriteSerializer(data=data)
        assert not serializer.is_valid()

    def test_inactive_product_rejected(self):
        """Produto inativo é rejeitado pelo queryset (active=True)."""
        product = ProductFactory(active=False)
        data = {'product': product.id, 'quantity': 5}
        serializer = SaleItemWriteSerializer(data=data)
        assert not serializer.is_valid()
        errors_str = str(serializer.errors)
        assert (
            'Produto inativo' in errors_str
            or 'Invalid pk' in errors_str
            or 'does not exist' in errors_str
            or 'Pk inválido' in errors_str
            or 'não existe' in errors_str
        ), errors_str
