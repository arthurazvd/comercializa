"""Relatórios de vendas e consulta de estoque, com exportação XLSX."""
from django.http import HttpResponse
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product
from .stock_lots import stock_snapshot
from .reports import filters_from_query, finance_report
from .xlsx_export import make_xlsx


def stock_status(p, today, snapshot=None):
    snapshot = snapshot if snapshot is not None else stock_snapshot(p, today)
    if not p.active:
        return 'inativo'
    if snapshot['expired_units']:
        return 'vencido'
    if snapshot['expiring_units']:
        return 'a_vencer'
    if snapshot['available_stock'] <= p.minimum_stock:
        return 'critico'
    return 'normal'


def stock_data():
    today = timezone.localdate()
    products = list(Product.objects.select_related('category').prefetch_related('lots').order_by('name', 'pk'))
    items = []
    for p in products:
        snap = stock_snapshot(p, today)
        status = stock_status(p, today, snap)
        items.append({'id': p.pk, 'name': p.name, 'sku': p.sku,
                      'category': p.category.name if p.category_id else 'Sem categoria',
                      'stock': p.stock, 'minimum_stock': p.minimum_stock,
                      'unit_cost': p.purchase_price, 'stock_value': snap['inventory_value'],
                      'average_cost': (snap['inventory_value'] / p.stock).quantize(Decimal('0.01')) if p.stock else p.purchase_price,
                      'expired_stock_value': snap['expired_stock_value'],
                      'expiration_date': snap['nearest_expiration'], 'active': p.active,
                      'available_stock': snap['available_stock'], 'expired_units': snap['expired_units'],
                      'expiring_units': snap['expiring_units'], 'lot_count': snap['lot_count'],
                      'status': status,
                      'low_stock': p.active and snap['available_stock'] <= p.minimum_stock,
                      'expired': p.active and snap['expired_units'] > 0,
                      'expiring': p.active and snap['expiring_units'] > 0})
    active = [i for i in items if i['active']]
    return {'summary': {'products': len(active), 'units': sum(i['stock'] for i in active),
                        'inventory_value': sum((i['stock_value'] for i in active), 0),
                        'expired_stock_value': sum((i['expired_stock_value'] for i in active), 0),
                        'available_units': sum(i['available_stock'] for i in active),
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
        rows = [(p['sku'] or '', p['name'], p['category'], p['stock'], p['available_stock'], p['expired_units'], p['expiring_units'], p['minimum_stock'],
                 p['average_cost'], p['unit_cost'], p['stock_value'], p['status'], p['expiration_date'] or '', p['lot_count'])
                for p in data['items']]
        summary = data['summary']
        sheets = [
            ('Estoque', ['SKU', 'Produto', 'Categoria', 'Saldo físico', 'Disponível', 'Vencido (un.)', 'A vencer (un.)', 'Mínimo', 'Custo médio (lotes)', 'Custo de referência', 'Valor estocado', 'Situação', 'Validade mais próxima', 'Lotes ativos'], rows, {8: 'currency', 9: 'currency', 10: 'currency'}),
            ('Resumo', ['Indicador', 'Valor'], [
                ('Produtos ativos', summary['products']), ('Unidades ativas', summary['units']),
                ('Valor do estoque (custo)', summary['inventory_value']),
                ('Unidades disponíveis para venda', summary['available_units']),
                ('Valor de unidades vencidas (custo)', summary['expired_stock_value']),
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
