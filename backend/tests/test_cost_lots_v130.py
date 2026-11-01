"""V1.3.0 — custo por recebimento, persistência histórica e posição financeira."""
from decimal import Decimal
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Product, Sale, SaleItem, StockLot, StockMovement


@pytest.fixture
def api():
    return APIClient()


@pytest.mark.django_db
def test_receipt_preserves_opening_cost_and_new_lot_cost(api):
    item = Product.objects.create(name='Boné', sku='BON-100', stock=4,
                                  purchase_price=5, sale_price=20)
    response = api.post('/api/stock-movements/', {
        'product': item.pk, 'delta': 3, 'note': 'Compra com novo preço',
        'justification': 'recebimento', 'unit_cost': '8.00',
        'update_reference_cost': True, 'new_sale_price': '25.00',
    }, format='json')
    assert response.status_code == 201, response.data
    item.refresh_from_db()
    assert item.stock == 7
    assert item.purchase_price == Decimal('8.00')
    assert item.sale_price == Decimal('25.00')
    batches = list(StockLot.objects.filter(product=item).order_by('pk'))
    assert len(batches) == 2
    assert [(b.received_quantity, b.unit_cost) for b in batches] == [
        (4, Decimal('5')), (3, Decimal('8')),
    ]
    assert batches[0].expiration_date is None and batches[1].expiration_date is None
    assert StockMovement.objects.get(pk=response.data['id']).unit_cost == Decimal('8.00')
    overview = api.get('/api/stock-overview/').data
    assert overview['summary']['inventory_value'] == Decimal('44.00')
    assert overview['items'][0]['stock_value'] == Decimal('44.00')
    assert overview['items'][0]['average_cost'] == Decimal('6.29')
    stock_lots = api.get(f'/api/products/{item.pk}/lots/').data
    assert {b['unit_cost'] for b in stock_lots} == {'5.00', '8.00'}


@pytest.mark.django_db
def test_sale_books_historical_cost_and_preserves_sale_price(api):
    item = Product.objects.create(name='Pote', stock=4, purchase_price=5, sale_price=20)
    added = api.post('/api/stock-movements/', {
        'product': item.pk, 'delta': 3, 'justification': 'recebimento',
        'note': 'Segunda compra', 'unit_cost': '8.00',
        'update_reference_cost': True,
    }, format='json')
    assert added.status_code == 201, added.data
    sold = api.post('/api/sales/', {
        'items': [{'product': item.pk, 'quantity': 5}],
    }, format='json')
    assert sold.status_code == 201, sold.data
    sale = Sale.objects.get(pk=sold.data['id'])
    line = SaleItem.objects.get(sale=sale)
    assert line.unit_price == Decimal('20')
    assert line.cost_total == Decimal('28.00')  # 4 x 5 + 1 x 8
    assert api.get('/api/stock-overview/').data['summary']['inventory_value'] == Decimal('16.00')
    item.refresh_from_db()
    assert item.stock == 2 and item.sale_price == Decimal('20')


@pytest.mark.django_db
def test_purchase_without_global_reference_change_isolated(api):
    item = Product.objects.create(name='Cabo', stock=3, purchase_price=9, sale_price=19)
    reply = api.post('/api/stock-movements/', {
        'product': item.pk, 'delta': 2, 'note': 'Fornecedor promocional',
        'justification': 'recebimento', 'unit_cost': '4.50',
        'update_reference_cost': False,
    }, format='json')
    assert reply.status_code == 201, reply.data
    item.refresh_from_db()
    assert item.purchase_price == Decimal('9')
    assert item.sale_price == Decimal('19')
    assert StockLot.objects.get(product=item).unit_cost == Decimal('4.50')
    assert api.get('/api/stock-overview/').data['summary']['inventory_value'] == Decimal('36.00')


@pytest.mark.django_db
def test_reject_expensive_receipt_without_valid_selling_price(api):
    item = Product.objects.create(name='Produto', stock=3, purchase_price=6, sale_price=15)
    payload = {'product': item.pk, 'delta': 2, 'note': 'Nova compra',
               'justification': 'recebimento', 'unit_cost': '17.00',
               'update_reference_cost': True}
    response = api.post('/api/stock-movements/', payload, format='json')
    assert response.status_code == 400
    item.refresh_from_db()
    assert item.stock == 3 and item.purchase_price == 6
    assert StockLot.objects.count() == 0
    fixed = api.post('/api/stock-movements/', {**payload, 'new_sale_price': '22.00'}, format='json')
    assert fixed.status_code == 201, fixed.data
    item.refresh_from_db()
    assert item.sale_price == Decimal('22.00')


@pytest.mark.django_db
def test_perishable_lots_preserve_expiration_and_cost(api):
    today = timezone.localdate()
    item = Product.objects.create(name='Chocolate', stock=0, purchase_price=2,
                                  sale_price=10, perishable=True)
    for expiry, cost in ((today + timedelta(days=3), '3.00'), (today + timedelta(days=8), '6.00')):
        response = api.post('/api/stock-movements/', {
            'product': item.pk, 'delta': 2, 'note': 'Recebimento',
            'expiration_date': expiry.isoformat(),
            'justification': 'recebimento', 'unit_cost': cost,
        }, format='json')
        assert response.status_code == 201, response.data
    assert api.get('/api/stock-overview/').data['summary']['inventory_value'] == Decimal('18.00')
    sold = api.post('/api/sales/', {'items': [{'product': item.pk, 'quantity': 3}]}, format='json')
    assert sold.status_code == 201, sold.data
    assert SaleItem.objects.get(sale_id=sold.data['id']).cost_total == Decimal('12.00')
    assert api.get('/api/stock-overview/').data['summary']['inventory_value'] == Decimal('6.00')


@pytest.mark.django_db
def test_edit_reference_cost_keeps_opening_balance_cost(api):
    item = Product.objects.create(name='Pilha', stock=5, purchase_price=3, sale_price=10)
    response = api.patch(f'/api/products/{item.pk}/', {'purchase_price': '7.00'}, format='json')
    assert response.status_code == 200, response.data
    lot = StockLot.objects.get(product=item)
    assert lot.quantity == 5 and lot.unit_cost == Decimal('3')
    assert api.get('/api/stock-overview/').data['summary']['inventory_value'] == Decimal('15.00')


@pytest.mark.django_db
def test_reversal_restores_original_purchase_cost(api):
    product = Product.objects.create(name='Marmita', stock=2, purchase_price=5, sale_price=15)
    response = api.post('/api/stock-movements/', {
        'product': product.pk, 'delta': 2, 'note': 'Nova remessa',
        'justification': 'recebimento', 'unit_cost': '8.00',
        'update_reference_cost': True,
    }, format='json')
    assert response.status_code == 201, response.data
    first_value = api.get('/api/stock-overview/').data['summary']['inventory_value']
    assert first_value == Decimal('26.00')
    sold = api.post('/api/sales/', {'items': [{'product': product.pk, 'quantity': 3}]}, format='json')
    assert sold.status_code == 201, sold.data
    assert SaleItem.objects.get(sale_id=sold.data['id']).cost_total == Decimal('18.00')
    canceled = api.post(f'/api/sales/{sold.data["id"]}/cancel/', {'reason': 'Cliente desistiu'}, format='json')
    assert canceled.status_code == 200, canceled.data
    assert api.get('/api/stock-overview/').data['summary']['inventory_value'] == first_value
    assert sorted((lot.quantity, lot.unit_cost) for lot in StockLot.objects.filter(product=product)) == [
        (2, Decimal('5.00')), (2, Decimal('8.00')),
    ]


@pytest.mark.django_db
def test_opening_balance_is_consumed_before_recent_receipts_even_if_sealed_later(api):
    product = Product.objects.create(name='Lápis', stock=3, purchase_price=2, sale_price=9)
    # Primeiro recebimento emite lote novo mas ainda não muda custo de referência.
    r1 = api.post('/api/stock-movements/', {
        'product': product.pk, 'delta': 2, 'note': 'Compra 1',
        'justification': 'recebimento', 'unit_cost': '4.00',
        'update_reference_cost': False,
    }, format='json')
    assert r1.status_code == 201, r1.data
    # A segunda compra fecha o saldo legado; seu PK é maior que o da compra 1.
    r2 = api.post('/api/stock-movements/', {
        'product': product.pk, 'delta': 1, 'note': 'Compra 2',
        'justification': 'recebimento', 'unit_cost': '5.00',
        'update_reference_cost': True,
    }, format='json')
    assert r2.status_code == 201, r2.data
    sale = api.post('/api/sales/', {'items': [{'product': product.pk, 'quantity': 4}]}, format='json')
    assert sale.status_code == 201, sale.data
    # 3 unidades do saldo antigo (2) e 1 da primeira compra (4).
    assert SaleItem.objects.get(sale_id=sale.data['id']).cost_total == Decimal('10.00')
