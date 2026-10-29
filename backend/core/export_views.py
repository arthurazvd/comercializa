"""Relatórios de vendas e consulta de estoque, com exportação XLSX."""
from django.http import HttpResponse
from datetime import timedelta
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product
from .reports import filters_from_query, finance_report
from .xlsx_export import make_xlsx


def stock_status(p, today):
    if not p.active:
        return 'inativo'
    if p.stock > 0 and p.expiration_date and p.expiration_date < today:
        return 'vencido'
    if p.stock > 0 and p.expiration_date and p.expiration_date <= today + timedelta(days=15):
        return 'a_vencer'
    if p.stock <= p.minimum_stock:
        return 'critico'
    return 'normal'


def stock_data():
    today = timezone.localdate()
    products = list(Product.objects.select_related('category').order_by('name', 'pk'))
    items = []
    for p in products:
        status = stock_status(p, today)
        items.append({'id': p.pk, 'name': p.name, 'sku': p.sku,
                      'category': p.category.name if p.category_id else 'Sem categoria',
                      'stock': p.stock, 'minimum_stock': p.minimum_stock,
                      'unit_cost': p.purchase_price, 'stock_value': p.stock * p.purchase_price,
                      'expiration_date': p.expiration_date, 'active': p.active,
                      'status': status,
                      'low_stock': p.active and p.stock <= p.minimum_stock,
                      'expired': p.active and p.stock > 0 and p.expiration_date is not None and p.expiration_date < today,
                      'expiring': p.active and p.stock > 0 and p.expiration_date is not None and today <= p.expiration_date <= today + timedelta(days=15)})
    active = [i for i in items if i['active']]
    return {'summary': {'products': len(active), 'units': sum(i['stock'] for i in active),
                        'inventory_value': sum((i['stock_value'] for i in active), 0),
                        'low_stock_count': sum(i['low_stock'] for i in active),
                        'expired_count': sum(i['expired'] for i in active),
                        'expiring_count': sum(i['expiring'] for i in active)}, 'items': items}


def excel_response(payload, filename):
    response = HttpResponse(payload, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


class StockOverviewView(APIView):
    def get(self, request):
        return Response(stock_data())


class StockExportView(APIView):
    def get(self, request):
        data = stock_data()
        rows = [(p['sku'] or '', p['name'], p['category'], p['stock'], p['minimum_stock'],
                 p['unit_cost'], p['stock_value'], p['status'], p['expiration_date'] or '')
                for p in data['items']]
        summary = data['summary']
        sheets = [
            ('Estoque', ['SKU', 'Produto', 'Categoria', 'Saldo', 'Mínimo', 'Custo unit.', 'Valor estocado', 'Situação', 'Validade'], rows, {5: 'currency', 6: 'currency'}),
            ('Resumo', ['Indicador', 'Valor'], [
                ('Produtos ativos', summary['products']), ('Unidades ativas', summary['units']),
                ('Valor do estoque (custo)', summary['inventory_value']),
                ('Estoque baixo', summary['low_stock_count']), ('Vencidos', summary['expired_count']),
                ('Vencendo em 15 dias', summary['expiring_count'])], {1: 'currency'}),
        ]
        return excel_response(make_xlsx(sheets), 'comercializa_estoque.xlsx')


class FinanceReportView(APIView):
    def get(self, request):
        filters = filters_from_query(request.query_params)
        return Response(finance_report(filters))


class FinanceExportView(APIView):
    def get(self, request):
        report = finance_report(filters_from_query(request.query_params))
        summary = report['summary']
        sheets = [
            ('Resumo financeiro', ['Indicador', 'Valor'], [
                ('Período inicial', report['filters']['start']), ('Período final', report['filters']['end']),
                ('Receita bruta', summary['gross']), ('Descontos rateados', summary['discounts']),
                ('Receita após descontos', summary['revenue']), ('Quantidade de vendas', summary['sales_count']),
                ('Unidades vendidas', summary['items_sold']), ('Ticket médio', summary['average_ticket'])], {1: 'currency'}),
            ('Produtos', ['Produto', 'Categoria', 'Unidades', 'Bruto', 'Descontos', 'Receita'], [
                (p['name'], p['category'], p['quantity'], p['gross'], p['discounts'], p['revenue'])
                for p in report['products']], {3: 'currency', 4: 'currency', 5: 'currency'}),
            ('Categorias', ['Categoria', 'Unidades', 'Receita'], [
                (c['name'], c['quantity'], c['revenue']) for c in report['categories']], {2: 'currency'}),
            ('Evolução diária', ['Data', 'Unidades', 'Receita'], [
                (d['date'], d['quantity'], d['revenue']) for d in report['daily']], {2: 'currency'}),
        ]
        return excel_response(make_xlsx(sheets), 'comercializa_financeiro.xlsx')
