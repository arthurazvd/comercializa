"""Testes de API: posição de estoque, filtros e planilhas Excel."""
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Category, Product, Sale, SaleItem, StockMovement
from core.reports import finance_report, filters_from_query
from core.xlsx_export import make_xlsx, col_label


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def catalog(db):
    cat = Category.objects.create(name='Utilidades domésticas')
    other_cat = Category.objects.create(name='Eletrônicos')
    p1 = Product.objects.create(name='Pote 1L', sku='TEST-POTE', category=cat,
                                purchase_price=4, sale_price=10, stock=2, minimum_stock=4)
    p2 = Product.objects.create(name='Carregador', sku='TEST-CABO', category=other_cat,
                                purchase_price=10, sale_price=20, stock=10, minimum_stock=3)
    return cat, other_cat, p1, p2


@pytest.mark.django_db
def test_stock_overview_exposes_summary_and_value(api_client, catalog):
    _, _, p1, p2 = catalog
    response = api_client.get('/api/stock-overview/')
    assert response.status_code == 200
    assert response.data['summary']['products'] == 2
    assert response.data['summary']['low_stock_count'] == 1
    assert response.data['summary']['inventory_value'] == Decimal('108')
    assert {p['status'] for p in response.data['items']} == {'critico', 'normal'}


@pytest.mark.django_db
def test_stock_overview_expired_and_expiring(api_client, catalog):
    _, _, p1, p2 = catalog
    p1.expiration_date = timezone.localdate() - timedelta(days=1)
    p1.save(update_fields=['expiration_date'])
    p2.expiration_date = timezone.localdate() + timedelta(days=4)
    p2.save(update_fields=['expiration_date'])
    response = api_client.get('/api/stock-overview/')
    assert response.data['summary']['expired_count'] == 1
    assert response.data['summary']['expiring_count'] == 1
    statuses = {p['id']: p['status'] for p in response.data['items']}
    assert statuses[p1.id] == 'vencido'
    assert statuses[p2.id] == 'a_vencer'


@pytest.mark.django_db
def test_finance_filters_discount_pro_rata(api_client, catalog):
    cat, other_cat, p1, p2 = catalog
    sale = Sale.objects.create(discount=Decimal('6.00'))
    SaleItem.objects.create(sale=sale, product=p1, quantity=1, unit_price=Decimal('10.00'))
    SaleItem.objects.create(sale=sale, product=p2, quantity=1, unit_price=Decimal('20.00'))
    today = timezone.localdate().isoformat()
    response = api_client.get('/api/reports/finance/', {'start': today, 'end': today})
    assert response.status_code == 200
    assert response.data['summary']['gross'] == Decimal('30.00')
    assert response.data['summary']['discounts'] == Decimal('6.00')
    assert response.data['summary']['revenue'] == Decimal('24.00')
    filtered = api_client.get('/api/reports/finance/', {'start': today, 'end': today, 'category': cat.id})
    assert filtered.data['summary']['gross'] == Decimal('10.00')
    assert filtered.data['summary']['discounts'] == Decimal('2.00')
    assert filtered.data['summary']['revenue'] == Decimal('8.00')
    assert filtered.data['summary']['sales_count'] == 1
    by_product = api_client.get('/api/reports/finance/', {'start': today, 'end': today, 'product': p2.id})
    assert by_product.data['summary']['revenue'] == Decimal('16.00')


@pytest.mark.django_db
def test_finance_uses_stored_sale_price_not_current_price(api_client, catalog):
    _, _, p1, _ = catalog
    sale = Sale.objects.create(discount=0)
    SaleItem.objects.create(sale=sale, product=p1, quantity=2, unit_price=Decimal('8.50'))
    p1.sale_price = 99
    p1.save(update_fields=['sale_price'])
    today = timezone.localdate().isoformat()
    report = api_client.get('/api/reports/finance/', {'start': today, 'end': today})
    assert report.data['summary']['revenue'] == Decimal('17.00')


@pytest.mark.django_db
def test_finance_rejects_invalid_dates_and_ids(api_client):
    for params in [
        {'start': '2026-02-31', 'end': '2026-03-01'},
        {'start': '2026-12-01', 'end': '2026-01-01'},
        {'start': '2000-01-01', 'end': '2026-01-01'},
        {'start': '2026-01-01', 'end': '2026-01-30', 'category': 'abc'},
        {'start': '2026-01-01', 'end': '2026-01-30', 'product': '-3'},
    ]:
        assert api_client.get('/api/reports/finance/', params).status_code == 400


@pytest.mark.django_db
def test_finance_empty_period(api_client):
    resp = api_client.get('/api/reports/finance/', {'start': '2024-02-01', 'end': '2024-02-29'})
    assert resp.data['summary']['revenue'] == Decimal('0.00')
    assert resp.data['products'] == []


def verify_xlsx(response, expected_sheets):
    assert response.status_code == 200
    assert 'spreadsheetml.sheet' in response['Content-Type']
    with ZipFile(BytesIO(response.content)) as archive:
        assert archive.testzip() is None
        ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        names = [s.attrib['name'] for s in workbook.findall('.//x:sheet', ns)]
        assert names == expected_sheets
        for index in range(1, len(expected_sheets) + 1):
            sheet = ET.fromstring(archive.read(f'xl/worksheets/sheet{index}.xml'))
            assert sheet.find('x:autoFilter', ns) is not None
            assert sheet.find('.//x:pane', ns) is not None


@pytest.mark.django_db
def test_excel_exports_produce_valid_zip(api_client, catalog):
    _, _, p1, _ = catalog
    sale = Sale.objects.create(discount=1)
    SaleItem.objects.create(sale=sale, product=p1, quantity=1, unit_price=10)
    verify_xlsx(api_client.get('/api/stock-export/'), ['Estoque', 'Resumo'])
    verify_xlsx(api_client.get('/api/reports/finance/export/'), ['Resumo financeiro', 'Produtos', 'Categorias', 'Evolução diária', 'Compras de estoque', 'Despesas', 'Investimentos'])


def test_excel_escapes_untrusted_text_and_formula_injection():
    assert col_label(1) == 'A' and col_label(27) == 'AA'
    data = make_xlsx([('Teste', ['Nome'], [('=HYPERLINK("x") < &',)], {})])
    with ZipFile(BytesIO(data)) as archive:
        xml = archive.read('xl/worksheets/sheet1.xml').decode()
        assert '=HYPERLINK' in xml
        assert '<f>' not in xml
        ET.fromstring(xml)


@pytest.mark.django_db
def test_seed_diverse_idempotent_and_non_destructive():
    call_command('seed_demo')
    total = Product.objects.count()
    assert total >= 30
    assert Product.objects.filter(name__icontains='Carregador').exists()
    assert Product.objects.filter(name__icontains='Boné').exists()
    assert Product.objects.filter(name__icontains='vasilhas').exists()
    product = Product.objects.get(sku='UTIL-001')
    product.stock = 99
    product.save(update_fields=['stock'])
    call_command('seed_demo')
    assert Product.objects.count() == total
    product.refresh_from_db()
    assert product.stock == 99

@pytest.mark.django_db
def test_seed_reset_is_audited_and_legacy_retired():
    call_command('seed_demo')
    old = Product.objects.create(name='Arroz 1kg', sku='ARROZ-01', sale_price=7, stock=5)
    p = Product.objects.get(sku='UTIL-001')
    initial = p.stock
    p.stock = 77
    p.save(update_fields=['stock'])
    call_command('seed_demo', reset_demo=True, retire_legacy=True)
    p.refresh_from_db()
    old.refresh_from_db()
    assert p.stock == initial
    assert old.active is False
    assert StockMovement.objects.filter(product=p, delta=initial - 77, note__icontains='catálogo demo').exists()
