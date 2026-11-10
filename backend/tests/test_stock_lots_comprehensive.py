"""Testes abrangentes para stock_lots.py - cobre todas as ramificações (happy/sad paths)."""
import inspect
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework import serializers

from core.models import Product, StockLot, StockMovement
from core.stock_lots import (
    _consume_available_lots,
    _eligible_stock,
    consume_lots,
    seal_legacy_stock,
    stock_snapshot,
)
from tests.factories import ProductFactory


@pytest.mark.django_db
class TestStockSnapshot:

    def test_snapshot_no_lots_no_expiration(self):
        product = ProductFactory(stock=100, expiration_date=None)
        snap = stock_snapshot(product, timezone.localdate())
        assert snap['available_stock'] == 100
        assert snap['expired_units'] == 0
        assert snap['expiring_units'] == 0
        assert snap['nearest_expiration'] is None
        assert snap['lot_count'] == 0
        assert snap['inventory_value'] == product.purchase_price * 100
        assert snap['expired_stock_value'] == Decimal('0')

    def test_snapshot_with_legacy_expiration_valid(self):
        product = ProductFactory(
            stock=100,
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        snap = stock_snapshot(product, timezone.localdate())
        assert snap['available_stock'] == 100
        assert snap['expired_units'] == 0
        assert snap['expiring_units'] == 0
        assert snap['nearest_expiration'] == product.expiration_date

    def test_snapshot_with_legacy_expiration_expired(self):
        product = ProductFactory(
            stock=100,
            expiration_date=timezone.localdate() - timedelta(days=5),
        )
        snap = stock_snapshot(product, timezone.localdate())
        assert snap['available_stock'] == 0
        assert snap['expired_units'] == 100
        assert snap['expiring_units'] == 0
        assert snap['nearest_expiration'] == product.expiration_date

    def test_snapshot_with_lots_valid(self):
        product = ProductFactory(stock=100)
        StockLot.objects.create(
            product=product, received_quantity=50, quantity=50,
            unit_cost=Decimal('10.00'),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('12.00'),
            expiration_date=timezone.localdate() + timedelta(days=60),
        )
        snap = stock_snapshot(product, timezone.localdate())
        assert snap['available_stock'] == 100
        assert snap['expired_units'] == 0
        assert snap['expiring_units'] == 0
        assert snap['lot_count'] == 2
        expected = Decimal('500') + Decimal('360') + \
            Decimal('20') * product.purchase_price
        assert snap['inventory_value'] == expected

    def test_snapshot_with_expired_lots(self):
        product = ProductFactory(stock=100)
        StockLot.objects.create(
            product=product, received_quantity=50, quantity=50,
            unit_cost=Decimal('10.00'),
            expiration_date=timezone.localdate() - timedelta(days=5),
        )
        StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('12.00'),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        snap = stock_snapshot(product, timezone.localdate())
        assert snap['available_stock'] == 50
        assert snap['expired_units'] == 50
        assert snap['expiring_units'] == 0
        assert snap['expired_stock_value'] == Decimal('500')

    def test_snapshot_with_lots_no_expiration(self):
        product = ProductFactory(stock=100)
        StockLot.objects.create(
            product=product, received_quantity=50, quantity=50,
            unit_cost=Decimal('10.00'), expiration_date=None,
        )
        snap = stock_snapshot(product, timezone.localdate())
        assert snap['available_stock'] == 100
        assert snap['expired_units'] == 0
        assert snap['expiring_units'] == 0
        assert snap['nearest_expiration'] is None

    def test_snapshot_mixed_legacy_and_lots(self):
        product = ProductFactory(
            stock=100,
            expiration_date=timezone.localdate() + timedelta(days=10),
        )
        StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('10.00'),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        snap = stock_snapshot(product, timezone.localdate())
        assert snap['available_stock'] == 100
        assert snap['expiring_units'] == 70
        assert snap['lot_count'] == 1

    def test_snapshot_zero_quantity_lots_ignored(self):
        product = ProductFactory(stock=100)
        StockLot.objects.create(
            product=product, received_quantity=50, quantity=0,
            unit_cost=Decimal('10.00'),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        snap = stock_snapshot(product, timezone.localdate())
        assert snap['lot_count'] == 0
        assert snap['available_stock'] == 100

    def test_snapshot_legacy_calculation(self):
        product = ProductFactory(stock=100)
        StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('10.00'),
        )
        StockLot.objects.create(
            product=product, received_quantity=20, quantity=20,
            unit_cost=Decimal('12.00'),
        )
        snap = stock_snapshot(product, timezone.localdate())
        assert snap['available_stock'] == 100
        expected = Decimal('300') + Decimal('240') + \
            Decimal('50') * product.purchase_price
        assert snap['inventory_value'] == expected


@pytest.mark.django_db
class TestEligibleStock:

    def test_eligible_stock_not_sale_only(self):
        product = ProductFactory(stock=100)
        lot1 = StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('10.00'),
            expiration_date=timezone.localdate() - timedelta(days=5),
        )
        lot2 = StockLot.objects.create(
            product=product, received_quantity=20, quantity=20,
            unit_cost=Decimal('12.00'),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        lots, legacy = _eligible_stock(
            product, [lot1, lot2], 50, timezone.localdate(),
            sale_only=False, quantity=10,
        )
        assert len(lots) == 2
        assert legacy == 50

    def test_eligible_stock_sale_only_filters_expired(self):
        product = ProductFactory(
            stock=100,
            expiration_date=timezone.localdate() + timedelta(days=10),
        )
        lot1 = StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('10.00'),
            expiration_date=timezone.localdate() - timedelta(days=5),
        )
        lot2 = StockLot.objects.create(
            product=product, received_quantity=20, quantity=20,
            unit_cost=Decimal('12.00'),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        lots, legacy = _eligible_stock(
            product, [lot1, lot2], 50, timezone.localdate(),
            sale_only=True, quantity=10,
        )
        assert len(lots) == 1
        assert lots[0].pk == lot2.pk
        assert legacy == 50

    def test_eligible_stock_sale_only_legacy_expired(self):
        product = ProductFactory(
            stock=100,
            expiration_date=timezone.localdate() - timedelta(days=5),
        )
        lot = StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('10.00'),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        lots, legacy = _eligible_stock(
            product, [lot], 70, timezone.localdate(),
            sale_only=True, quantity=10,
        )
        assert len(lots) == 1
        assert legacy == 0

    def test_eligible_stock_insufficient_raises(self):
        product = ProductFactory(
            stock=100,
            expiration_date=timezone.localdate() - timedelta(days=5),
        )
        lot = StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('10.00'),
            expiration_date=timezone.localdate() - timedelta(days=10),
        )
        with pytest.raises(serializers.ValidationError) as exc:
            _eligible_stock(
                product, [lot], 70, timezone.localdate(),
                sale_only=True, quantity=10,
            )
        assert 'Estoque válido insuficiente' in str(exc.value)


@pytest.mark.django_db
class TestConsumeAvailableLots:

    def test_consume_single_lot(self):
        product = ProductFactory()
        lot = StockLot.objects.create(
            product=product, received_quantity=50, quantity=50,
            unit_cost=Decimal('10.00'),
        )
        consumed, remaining = _consume_available_lots([lot], 30)
        assert len(consumed) == 1
        assert consumed[0][1] == 30
        assert remaining == 0
        lot.refresh_from_db()
        assert lot.quantity == 20

    def test_consume_multiple_lots(self):
        product = ProductFactory()
        lot1 = StockLot.objects.create(
            product=product, received_quantity=20, quantity=20,
            unit_cost=Decimal('10.00'),
        )
        lot2 = StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('12.00'),
        )
        consumed, remaining = _consume_available_lots([lot1, lot2], 40)
        assert len(consumed) == 2
        assert consumed[0][1] == 20
        assert consumed[1][1] == 20
        assert remaining == 0
        lot1.refresh_from_db()
        assert lot1.quantity == 0
        lot2.refresh_from_db()
        assert lot2.quantity == 10

    def test_consume_more_than_available(self):
        product = ProductFactory()
        lot = StockLot.objects.create(
            product=product, received_quantity=20, quantity=20,
            unit_cost=Decimal('10.00'),
        )
        consumed, remaining = _consume_available_lots([lot], 50)
        assert len(consumed) == 1
        assert consumed[0][1] == 20
        assert remaining == 30

    def test_consume_concurrent_modification_raises(self):
        product = ProductFactory()
        lot = StockLot.objects.create(
            product=product, received_quantity=50, quantity=50,
            unit_cost=Decimal('10.00'),
        )
        StockLot.objects.filter(pk=lot.pk).update(quantity=10)
        with pytest.raises(serializers.ValidationError) as exc:
            _consume_available_lots([lot], 30)
        assert 'Lote alterado simultaneamente' in str(exc.value)


@pytest.mark.django_db
class TestConsumeLots:

    def test_consume_lots_sale_only(self):
        product = ProductFactory(
            stock=100,
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        lot = StockLot.objects.create(
            product=product, received_quantity=50, quantity=50,
            unit_cost=Decimal('10.00'),
            expiration_date=timezone.localdate() + timedelta(days=60),
        )
        consumed = consume_lots(product, 30, sale_only=True)
        assert len(consumed) == 1
        assert consumed[0][1] == 30
        lot.refresh_from_db()
        assert lot.quantity == 20

    def test_consume_lots_not_sale_only(self):
        product = ProductFactory(stock=100)
        lot = StockLot.objects.create(
            product=product, received_quantity=50, quantity=50,
            unit_cost=Decimal('10.00'),
            expiration_date=timezone.localdate() - timedelta(days=5),
        )
        consumed = consume_lots(product, 30, sale_only=False)
        assert len(consumed) == 1
        assert consumed[0][1] == 30

    def test_consume_lots_legacy_fallback(self):
        product = ProductFactory(
            stock=100,
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        StockLot.objects.create(
            product=product, received_quantity=20, quantity=20,
            unit_cost=Decimal('10.00'),
        )
        consumed = consume_lots(product, 50, sale_only=True)
        assert len(consumed) == 1
        assert consumed[0][1] == 20
        product.refresh_from_db()
        assert product.stock == 100

    def test_consume_lots_insufficient_legacy_raises(self):
        product = ProductFactory(
            stock=30,
            expiration_date=timezone.localdate() - timedelta(days=5),
        )
        StockLot.objects.create(
            product=product, received_quantity=20, quantity=20,
            unit_cost=Decimal('10.00'),
            expiration_date=timezone.localdate() - timedelta(days=10),
        )
        with pytest.raises(serializers.ValidationError) as exc:
            consume_lots(product, 10, sale_only=True)
        assert 'Estoque válido insuficiente' in str(exc.value)

    def test_consume_lots_fefo_order(self):
        product = ProductFactory(stock=100)
        lot1 = StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('10.00'),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        lot2 = StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('12.00'),
            expiration_date=timezone.localdate() + timedelta(days=10),
        )
        StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('15.00'),
            expiration_date=timezone.localdate() + timedelta(days=60),
        )
        consumed = consume_lots(product, 50, sale_only=True)
        assert consumed[0][0].pk == lot2.pk
        assert consumed[0][1] == 30
        assert consumed[1][0].pk == lot1.pk
        assert consumed[1][1] == 20

    def test_consume_lots_opening_balance_priority(self):
        product = ProductFactory(stock=100)
        lot1 = StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('10.00'),
            expiration_date=timezone.localdate() + timedelta(days=30),
            receipt_movement=None,
        )
        movement = StockMovement.objects.create(
            product=product, delta=30, stock_before=0, stock_after=30,
            reason='adjustment',
        )
        StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('12.00'),
            expiration_date=timezone.localdate() + timedelta(days=30),
            receipt_movement=movement,
        )
        consumed = consume_lots(product, 30, sale_only=True)
        assert consumed[0][0].pk == lot1.pk


@pytest.mark.django_db
class TestSealLegacyStock:

    def test_seal_legacy_creates_opening_lot(self):
        product = ProductFactory(stock=100, purchase_price=Decimal('15.00'))
        initial_lots = product.lots.count()
        legacy = seal_legacy_stock(product)
        assert legacy == 100
        assert product.lots.count() == initial_lots + 1
        opening_lot = (
            product.lots
            .filter(receipt_movement__isnull=True)
            .order_by('-id')
            .first()
        )
        assert opening_lot is not None
        assert opening_lot.quantity == 100
        assert opening_lot.unit_cost == Decimal('15.00')
        assert opening_lot.expiration_date == product.expiration_date

    def test_seal_legacy_no_legacy_stock(self):
        product = ProductFactory(stock=50)
        StockLot.objects.create(
            product=product, received_quantity=50, quantity=50,
            unit_cost=Decimal('10.00'),
        )
        legacy = seal_legacy_stock(product)
        assert legacy == 0
        assert product.lots.count() == 1

    def test_seal_legacy_partial_legacy(self):
        product = ProductFactory(stock=100, purchase_price=Decimal('15.00'))
        StockLot.objects.create(
            product=product, received_quantity=30, quantity=30,
            unit_cost=Decimal('10.00'),
        )
        legacy = seal_legacy_stock(product)
        assert legacy == 70
        opening_lot = (
            product.lots
            .filter(receipt_movement__isnull=True)
            .order_by('-id')
            .first()
        )
        assert opening_lot.quantity == 70
        assert opening_lot.unit_cost == Decimal('15.00')

    def test_seal_legacy_idempotent(self):
        product = ProductFactory(stock=100, purchase_price=Decimal('15.00'))
        legacy1 = seal_legacy_stock(product)
        legacy2 = seal_legacy_stock(product)
        assert legacy1 == 100
        assert legacy2 == 0
        assert product.lots.filter(receipt_movement__isnull=True).count() == 1

    def test_seal_legacy_with_select_for_update(self):
        source = inspect.getsource(seal_legacy_stock)
        assert 'select_for_update' in source


@pytest.mark.django_db
class TestStockLotsIntegration:

    def test_full_cycle_receipt_seal_consume(self):
        product = ProductFactory(stock=50, purchase_price=Decimal('10.00'))
        StockLot.objects.create(
            product=product, received_quantity=50, quantity=50,
            unit_cost=Decimal('12.00'),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        Product.objects.filter(pk=product.pk).update(stock=100)
        product.refresh_from_db()

        old_purchase = product.purchase_price
        seal_legacy_stock(product)

        Product.objects.filter(pk=product.pk).update(
            purchase_price=Decimal('15.00'))
        product.refresh_from_db()

        opening_lot = (
            product.lots
            .filter(receipt_movement__isnull=True, unit_cost=old_purchase)
            .first()
        )
        assert opening_lot is not None
        assert opening_lot.unit_cost == old_purchase

        consumed = consume_lots(product, 60, sale_only=True)
        assert len(consumed) == 2
        lot_quantities = [qty for _, qty in consumed]
        assert 50 in lot_quantities
        assert 10 in lot_quantities