"""Entradas e baixas por lote, preservação de legado e atomicidade."""
from datetime import timedelta
from django.utils import timezone
import pytest
from rest_framework.test import APIClient

from core.models import Product, StockLot, StockLotAllocation, StockMovement


@pytest.fixture
def client_api():
    return APIClient()


@pytest.fixture
def perishable(db):
    return Product.objects.create(name='Chocolate artesanal', sku='LOTE-CHOCO', perishable=True,
                                  sale_price=10, purchase_price=4, stock=3, minimum_stock=2,
                                  expiration_date=timezone.localdate() - timedelta(days=2))


@pytest.mark.django_db
def test_receipt_creates_lot_and_preserves_legacy_expiration(client_api, perishable):
    old_date = perishable.expiration_date
    later = timezone.localdate() + timedelta(days=40)
    response = client_api.post('/api/stock-movements/', {
        'product': perishable.pk, 'delta': 5, 'note': 'Recebimento de fornecedor',
        'expiration_date': later.isoformat(), 'justification': 'recebimento',
    }, format='json')
    assert response.status_code == 201, response.data
    perishable.refresh_from_db()
    assert perishable.stock == 8
    assert perishable.expiration_date == old_date
    lot = StockLot.objects.get(product=perishable)
    assert lot.quantity == 5 and lot.expiration_date == later
    assert lot.receipt_movement_id == response.data['id']
    assert response.data['justification'] == 'recebimento'
    assert response.data['lots'] == [{'expiration_date': later, 'quantity': 5}]
    product_response = client_api.get(f'/api/products/{perishable.id}/').data
    assert product_response['available_stock'] == 5
    assert product_response['expired_units'] == 3
    overview = client_api.get('/api/stock-overview/').data['summary']
    assert overview['expired_count'] == 1
    assert overview['expired_stock_value'] == 12
    assert overview['available_units'] == 5


@pytest.mark.django_db
def test_perishable_requires_new_expiration_and_rejects_expired_lot(client_api, perishable):
    base = {'product': perishable.pk, 'delta': 5, 'note': 'Recebimento'}
    assert client_api.post('/api/stock-movements/', base, format='json').status_code == 400
    assert client_api.post('/api/stock-movements/', {**base, 'expiration_date': '2020-01-01'}, format='json').status_code == 400
    assert client_api.post('/api/stock-movements/', {**base, 'delta': -1, 'expiration_date': '2030-01-01'}, format='json').status_code == 400
    perishable.refresh_from_db()
    assert perishable.stock == 3
    assert StockLot.objects.count() == 0


@pytest.mark.django_db
def test_sale_consumes_nearest_valid_lot_and_keeps_expired_legacy(client_api, perishable):
    today = timezone.localdate()
    first = StockLot.objects.create(product=perishable, expiration_date=today + timedelta(days=3), quantity=2, received_quantity=2)
    second = StockLot.objects.create(product=perishable, expiration_date=today + timedelta(days=30), quantity=4, received_quantity=4)
    perishable.stock = 9  # 3 legadas vencidas + 6 loteados válidos
    perishable.save(update_fields=['stock'])
    response = client_api.post('/api/sales/', {'items': [{'product': perishable.id, 'quantity': 4}], 'discount': 0}, format='json')
    assert response.status_code == 201, response.data
    first.refresh_from_db(); second.refresh_from_db(); perishable.refresh_from_db()
    assert (first.quantity, second.quantity, perishable.stock) == (0, 2, 5)
    assert [(a.lot_id, a.quantity) for a in StockLotAllocation.objects.order_by('lot_id')] == [(first.pk, 2), (second.pk, 2)]
    assert client_api.get(f'/api/products/{perishable.pk}/').data['available_stock'] == 2
    blocked = client_api.post('/api/sales/', {'items': [{'product': perishable.id, 'quantity': 3}], 'discount': 0}, format='json')
    assert blocked.status_code == 400
    perishable.refresh_from_db()
    assert perishable.stock == 5


@pytest.mark.django_db
def test_disposal_of_expired_lot_is_permitted_and_audited(client_api, perishable):
    today = timezone.localdate()
    lot = StockLot.objects.create(product=perishable, expiration_date=today - timedelta(days=1), quantity=4, received_quantity=4)
    perishable.stock = 7
    perishable.save(update_fields=['stock'])
    response = client_api.post('/api/stock-movements/', {'product': perishable.pk, 'delta': -4, 'note': 'Descarte por vencimento'}, format='json')
    assert response.status_code == 201, response.data
    lot.refresh_from_db(); perishable.refresh_from_db()
    assert lot.quantity == 0 and perishable.stock == 3
    assert StockLotAllocation.objects.get(movement_id=response.data['id']).quantity == 4


@pytest.mark.django_db
def test_nonperishable_legacy_sale_still_works(client_api, db):
    p = Product.objects.create(name='Boné', sku='LOTE-BONE', stock=5, sale_price=15)
    response = client_api.post('/api/sales/', {'items': [{'product': p.pk, 'quantity': 2}], 'discount': 0}, format='json')
    assert response.status_code == 201, response.data
    p.refresh_from_db()
    assert p.stock == 3
    assert not StockLot.objects.exists()


@pytest.mark.django_db
def test_product_edit_decrements_tracked_stock(client_api, perishable):
    lot = StockLot.objects.create(product=perishable, expiration_date=timezone.localdate() + timedelta(days=10), quantity=2, received_quantity=2)
    perishable.stock = 5
    perishable.save(update_fields=['stock'])
    response = client_api.patch(f'/api/products/{perishable.pk}/', {'stock': 3}, format='json')
    assert response.status_code == 200, response.data
    lot.refresh_from_db()
    assert lot.quantity == 0
    assert StockLotAllocation.objects.filter(movement__reason=StockMovement.Reason.ADJUSTMENT, lot=lot, quantity=2).exists()


@pytest.mark.django_db
def test_perishable_stock_cannot_be_increased_directly(client_api, perishable):
    response = client_api.patch(f'/api/products/{perishable.pk}/', {'stock': 6}, format='json')
    assert response.status_code == 400
    assert 'Movimentações' in str(response.data)
    perishable.refresh_from_db()
    assert perishable.stock == 3


@pytest.mark.django_db
def test_demo_marks_expiring_items_as_perishable(client_api, db):
    from django.core.management import call_command
    call_command('seed_demo')
    assert Product.objects.get(sku='BELE-003').perishable is True
    assert Product.objects.get(sku='BELE-004').perishable is True
    assert Product.objects.get(sku='UTIL-001').perishable is False


@pytest.mark.django_db
def test_justification_is_validated_server_side(client_api, db):
    p = Product.objects.create(name='Chapéu', sku='JUST-01', sale_price=10, stock=4)
    bad = client_api.post('/api/stock-movements/', {'product': p.pk, 'delta': -1,
        'note': 'Recebimento', 'justification': 'recebimento'}, format='json')
    assert bad.status_code == 400
    good = client_api.post('/api/stock-movements/', {'product': p.pk, 'delta': -1,
        'note': 'Peça quebrada', 'justification': 'avaria'}, format='json')
    assert good.status_code == 201
    assert good.data['justification'] == 'avaria'
