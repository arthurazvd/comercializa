"""V1.4.0 — margem por custo histórico, despesas, compras e Excel.

Os testes protegem contra tratar compras de estoque como despesas novamente,
contra reatribuir custo de lote anterior e contra afirmar lucro líquido.
"""
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import Product, Sale, SaleItem, FinancialEntry


@pytest.fixture
def client_api():
    return APIClient()


def today():
    return timezone.localdate().isoformat()


def report(client_api, **extra):
    return client_api.get('/api/reports/finance/', {'start': today(), 'end': today(), **extra})


@pytest.mark.django_db
def test_faturamento_cmv_lucro_bruto_desconto_e_custos_de_lotes(client_api):
    item = Product.objects.create(name='Copo', purchase_price=4, sale_price=10, stock=3)
    receipt = client_api.post('/api/stock-movements/', {
        'product': item.pk, 'delta': 3, 'note': 'Nova compra',
        'justification': 'recebimento', 'unit_cost': '6.00',
    }, format='json')
    assert receipt.status_code == 201, receipt.data
    sale = client_api.post('/api/sales/', {
        'items': [{'product': item.pk, 'quantity': 4}], 'discount': '4.00',
    }, format='json')
    assert sale.status_code == 201, sale.data
    result = report(client_api)
    assert result.status_code == 200, result.data
    s = result.data['summary']
    assert s['gross'] == Decimal('40.00')
    assert s['discounts'] == Decimal('4.00')
    assert s['revenue'] == Decimal('36.00')
    assert s['cogs'] == Decimal('18.00')  # 3x4 + 1x6
    assert s['gross_profit'] == Decimal('18.00')
    assert s['gross_margin_percentage'] == Decimal('50.00')
    assert s['operating_result'] == Decimal('18.00')
    assert s['purchase_total'] == Decimal('18.00')
    assert s['registered_outlays'] == Decimal('18.00')
    assert s['estimated_cost_lines'] == 0
    assert result.data['products'][0]['gross_profit'] == Decimal('18.00')
    assert result.data['categories'][0]['cogs'] == Decimal('18.00')
    assert result.data['daily'][0]['gross_profit'] == Decimal('18.00')


@pytest.mark.django_db
def test_opex_resultado_e_capex_nao_duplicam_cmvs(client_api):
    item = Product.objects.create(name='Boné', stock=2, purchase_price=7, sale_price=20)
    sale = client_api.post('/api/sales/', {'items': [{'product': item.pk, 'quantity': 1}]}, format='json')
    assert sale.status_code == 201
    for kind, amount, desc in [('expense','3.00','Energia elétrica'), ('investment','80.00','Comprar balcão')]:
        posted = client_api.post('/api/finance/entries/', {
            'kind': kind, 'category': 'outros', 'description': desc,
            'amount': amount, 'entry_date': today(),
        }, format='json')
        assert posted.status_code == 201, posted.data
    s = report(client_api).data['summary']
    assert s['revenue'] == Decimal('20.00')
    assert s['cogs'] == Decimal('7.00')
    assert s['gross_profit'] == Decimal('13.00')
    assert s['expense_total'] == Decimal('3.00')
    assert s['operating_result'] == Decimal('10.00')
    assert s['capital_investments'] == Decimal('80.00')
    assert s['registered_outlays'] == Decimal('83.00')


@pytest.mark.django_db
def test_produto_filtrado_nao_recebe_custo_operacional_geral(client_api):
    item = Product.objects.create(name='Linha', stock=1, purchase_price=3, sale_price=8)
    client_api.post('/api/sales/', {'items': [{'product': item.pk, 'quantity': 1}]}, format='json')
    client_api.post('/api/finance/entries/', {
        'kind': 'expense', 'category': 'aluguel', 'description': 'Aluguel do ponto',
        'amount': '100.00', 'entry_date': today(),
    }, format='json')
    result = report(client_api, product=item.pk)
    assert result.data['summary']['gross_profit'] == Decimal('5.00')
    assert result.data['summary']['company_scope'] is False
    assert result.data['summary']['operating_result'] is None
    assert result.data['expenses'] == []


@pytest.mark.django_db
def test_estorno_de_venda_remove_receita_e_cmv(client_api):
    item = Product.objects.create(name='Caneca', stock=2, purchase_price=8, sale_price=13)
    sale = client_api.post('/api/sales/', {'items': [{'product': item.pk, 'quantity': 1}]}, format='json')
    assert report(client_api).data['summary']['cogs'] == Decimal('8.00')
    reversal = client_api.post(f'/api/sales/{sale.data["id"]}/cancel/', {'reason': 'Cliente desistiu'}, format='json')
    assert reversal.status_code == 200, reversal.data
    summary = report(client_api).data['summary']
    assert summary['revenue'] == Decimal('0.00')
    assert summary['cogs'] == Decimal('0.00')
    assert summary['gross_profit'] == Decimal('0.00')


@pytest.mark.django_db
def test_anular_despesa_preserva_historico_sem_afetar_estoque(client_api):
    posted = client_api.post('/api/finance/entries/', {
        'kind':'expense', 'category':'marketing', 'description':'Tráfego pago',
        'amount':'25.00', 'entry_date':today(),
    }, format='json')
    assert posted.status_code == 201
    entry_id = posted.data['id']
    assert report(client_api).data['summary']['expense_total'] == Decimal('25.00')
    voided = client_api.post(f'/api/finance/entries/{entry_id}/void/', {}, format='json')
    again = client_api.post(f'/api/finance/entries/{entry_id}/void/', {}, format='json')
    assert voided.status_code == again.status_code == 200
    assert FinancialEntry.objects.get(pk=entry_id).voided_at is not None
    assert report(client_api).data['summary']['expense_total'] == Decimal('0.00')


@pytest.mark.django_db
def test_lancamento_rejeita_valores_negativos_e_descricoes_vazias(client_api):
    for data in (
        {'kind':'expense', 'category':'outros', 'description':'Teste', 'amount':'-3.00', 'entry_date':today()},
        {'kind':'expense', 'category':'outros', 'description':'  ', 'amount':'10.00', 'entry_date':today()},
        {'kind':'wrong', 'category':'outros', 'description':'Coisa', 'amount':'10.00', 'entry_date':today()},
    ):
        response = client_api.post('/api/finance/entries/', data, format='json')
        assert response.status_code == 400
    assert FinancialEntry.objects.count() == 0


@pytest.mark.django_db
def test_lancamento_idempotente_na_api(client_api):
    payload={'kind':'expense', 'category':'outros', 'description':'Água mineral', 'amount':'5.00', 'entry_date':today()}
    key='expense-idempotency-test-12345'
    one=client_api.post('/api/finance/entries/', payload, format='json', HTTP_IDEMPOTENCY_KEY=key)
    two=client_api.post('/api/finance/entries/', payload, format='json', HTTP_IDEMPOTENCY_KEY=key)
    assert one.status_code == two.status_code == 201
    assert one.data['id'] == two.data['id']
    assert FinancialEntry.objects.count() == 1


@pytest.mark.django_db
def test_cost_missing_from_old_sale_is_labeled_estimated(client_api):
    item=Product.objects.create(name='Legacy', purchase_price=12, sale_price=20)
    sale=Sale.objects.create(discount=0)
    SaleItem.objects.create(sale=sale, product=item, quantity=1, unit_price=20, cost_total=None)
    result=report(client_api)
    assert result.data['summary']['cogs'] == Decimal('12.00')
    assert result.data['summary']['estimated_cost_lines'] == 1


@pytest.mark.django_db
def test_export_financeiro_gera_sete_abas_e_nao_executa_formulas(client_api):
    item=Product.objects.create(name='=HYPERLINK("a")', purchase_price=1, sale_price=2)
    sale=Sale.objects.create(discount=0)
    SaleItem.objects.create(sale=sale, product=item, quantity=1, unit_price=2, cost_total=1)
    response=client_api.get('/api/reports/finance/export/', {'start':today(),'end':today()})
    assert response.status_code == 200
    with ZipFile(BytesIO(response.content)) as archive:
        assert archive.testzip() is None
        sheet_names=archive.read('xl/workbook.xml').decode('utf-8')
        for name in ('Resumo financeiro','Produtos','Categorias','Evolução diária','Compras de estoque','Despesas','Investimentos'):
            assert name in sheet_names
        products_xml=archive.read('xl/worksheets/sheet2.xml').decode('utf-8')
        assert '=HYPERLINK' in products_xml
        assert '<f>' not in products_xml
