"""Regras essenciais do estorno integral: reversão financeira, estoque e auditoria."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Product, Sale, StockLot, StockLotAllocation, StockMovement
from core.reports import finance_report


@pytest.fixture
def api():
    return APIClient()


@pytest.mark.django_db
def test_full_reversal_restores_stock_and_removes_revenue(api):
    product = Product.objects.create(name='Carrinho', sale_price='30.00', stock=8, minimum_stock=0)
    sale_response = api.post('/api/sales/', {
        'discount': '5.00', 'items': [{'product': product.pk, 'quantity': 2}],
    }, format='json')
    assert sale_response.status_code == 201, sale_response.data
    sale_id = sale_response.data['id']
    product.refresh_from_db()
    assert product.stock == 6
    filters = {'start': timezone.localdate(), 'end': timezone.localdate()}
    assert finance_report(filters)['summary']['revenue'] == Decimal('55.00')

    cancel = api.post(f'/api/sales/{sale_id}/cancel/', {'reason': 'Devolução integral'}, format='json')
    assert cancel.status_code == 200, cancel.data
    assert cancel.data['canceled_at'] is not None
    assert Decimal(cancel.data['refunded_amount']) == Decimal('55.00')
    assert cancel.data['cancellation_reason'] == 'Devolução integral'
    product.refresh_from_db()
    assert product.stock == 8
    assert Sale.objects.get(pk=sale_id).canceled_at is not None
    movements = list(StockMovement.objects.filter(sale_id=sale_id).order_by('id'))
    assert len(movements) == 2
    assert [(m.reason, m.delta, m.stock_before, m.stock_after) for m in movements] == [
        ('sale', -2, 8, 6), ('reversal', 2, 6, 8),
    ]
    report = finance_report(filters)
    assert report['summary']['revenue'] == Decimal('0.00')
    assert report['summary']['sales_count'] == 0
    assert api.get('/api/dashboard/').data['summary']['sales_count'] == 0

    # Repetir mesmo se a API perdeu a primeira resposta jamais devolve duas vezes.
    second = api.post(f'/api/sales/{sale_id}/cancel/', {'reason': 'Mudança indevida'}, format='json')
    assert second.status_code == 200
    product.refresh_from_db()
    assert product.stock == 8
    assert StockMovement.objects.filter(sale_id=sale_id).count() == 2
    assert second.data['cancellation_reason'] == 'Devolução integral'


@pytest.mark.django_db
def test_lot_reversal_returns_quantities_to_original_lots(api):
    product = Product.objects.create(name='Doce', sale_price='10.00', perishable=True, stock=6)
    today = timezone.localdate()
    first = StockLot.objects.create(product=product, expiration_date=today + timedelta(days=3),
                                    received_quantity=2, quantity=2)
    second = StockLot.objects.create(product=product, expiration_date=today + timedelta(days=40),
                                     received_quantity=4, quantity=4)
    created = api.post('/api/sales/', {'items': [{'product': product.pk, 'quantity': 4}]}, format='json')
    assert created.status_code == 201, created.data
    first.refresh_from_db(); second.refresh_from_db()
    assert (first.quantity, second.quantity) == (0, 2)
    reversed_sale = api.post(f'/api/sales/{created.data["id"]}/cancel/', {'reason': 'Devolução'}, format='json')
    assert reversed_sale.status_code == 200, reversed_sale.data
    first.refresh_from_db(); second.refresh_from_db(); product.refresh_from_db()
    assert (first.quantity, second.quantity, product.stock) == (2, 4, 6)
    restored = StockMovement.objects.get(sale_id=created.data['id'], reason='reversal')
    assert sorted((a.lot_id, a.quantity) for a in restored.lot_allocations.all()) == [(first.pk, 2), (second.pk, 2)]
    fetched = api.get('/api/stock-movements/').data
    record = next(entry for entry in fetched if entry['id'] == restored.pk)
    assert sorted(entry['quantity'] for entry in record['lots']) == [2, 2]


@pytest.mark.django_db
def test_reversal_validates_reason_and_never_changes_stock_on_error(api):
    product = Product.objects.create(name='Teste', sale_price='10.00', stock=5)
    created = api.post('/api/sales/', {'items': [{'product': product.pk, 'quantity': 2}]}, format='json')
    sale_id = created.data['id']
    invalid = api.post(f'/api/sales/{sale_id}/cancel/', {'reason': ' '}, format='json')
    assert invalid.status_code == 400
    assert Sale.objects.get(pk=sale_id).canceled_at is None
    product.refresh_from_db()
    assert product.stock == 3
    assert api.post('/api/sales/9999999/cancel/', {'reason': 'Erro de venda'}, format='json').status_code == 404


@pytest.mark.django_db
def test_operation_confirmation_returns_original_committed_response(api):
    product = Product.objects.create(name='Carro', sale_price='10.00', stock=9)
    key = 'operation_confirmation_test_0123456789'
    created = api.post('/api/sales/', {'items': [{'product': product.pk, 'quantity': 2}]},
                       format='json', HTTP_IDEMPOTENCY_KEY=key)
    assert created.status_code == 201
    confirmed = api.get(f'/api/operations/{key}/')
    assert confirmed.status_code == 200, confirmed.data
    assert confirmed.data['confirmed'] is True
    assert confirmed.data['data']['id'] == created.data['id']
    assert confirmed.data['path'] == '/api/sales/'
    assert confirmed.data['status'] == 201
    assert api.get('/api/operations/not_existing_key/').status_code == 404
