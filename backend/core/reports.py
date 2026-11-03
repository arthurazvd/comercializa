"""Consultas financeiras filtradas. Descontos são rateados entre itens da venda.

Receita líquida aqui significa *venda menos descontos*; não é lucro líquido.
"""
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Sale, StockMovement, FinancialEntry

CENT = Decimal('0.01')


def money(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def filters_from_query(params):
    today = timezone.localdate()
    default_start = today.replace(day=1)
    start_raw = params.get('start', default_start.isoformat())
    end_raw = params.get('end', today.isoformat())
    try:
        start, end = date.fromisoformat(start_raw), date.fromisoformat(end_raw)
    except (ValueError, TypeError):
        raise ValidationError({'dates': 'Informe datas válidas em AAAA-MM-DD.'})
    if start > end:
        raise ValidationError({'dates': 'A data inicial não pode superar a final.'})
    if (end - start).days > 3660:
        raise ValidationError({'dates': 'O intervalo máximo é de dez anos.'})
    ids = {}
    for key in ('category', 'product'):
        raw = params.get(key, '')
        if raw not in ('', None):
            try:
                value = int(raw)
                if value <= 0:
                    raise ValueError
                ids[key] = value
            except (ValueError, TypeError):
                raise ValidationError({key: 'Informe um ID inteiro positivo.'})
    return {'start': start, 'end': end, **ids}


def _selected_items(items, filters):
    return [item for item in items
            if ('category' not in filters or item.product.category_id == filters['category'])
            and ('product' not in filters or item.product_id == filters['product'])]


def _line_cost(item):
    if item.cost_total is not None:
        return item.cost_total, False
    return item.product.purchase_price * item.quantity, True


def _accumulate_row(target, amount, discount, cost, quantity):
    target['gross'] += amount
    target['discount'] += discount
    target['cost'] += cost
    target['quantity'] += quantity


def _empty_sales_group():
    return {'quantity': 0, 'gross': Decimal('0'), 'discount': Decimal('0'), 'cost': Decimal('0')}


def _accumulate_sale(sale, filters, by_product, by_category, by_day):
    items = list(sale.items.all())
    selected = _selected_items(items, filters)
    if not selected:
        return None
    total_gross = sum((item.unit_price * item.quantity for item in items), Decimal('0'))
    day = timezone.localtime(sale.created_at).date().isoformat()
    gross = discount = cost_total = Decimal('0')
    quantity = estimated_count = 0
    for item in selected:
        amount = item.unit_price * item.quantity
        portion = sale.discount * amount / total_gross if total_gross else Decimal('0')
        cost, estimated = _line_cost(item)
        gross += amount
        discount += portion
        quantity += item.quantity
        cost_total += cost
        estimated_count += int(estimated)
        category = item.product.category.name if item.product.category_id else 'Sem categoria'
        product_key = (item.product_id, item.product.name, category)
        for group in (by_product[product_key], by_category[category], by_day[day]):
            _accumulate_row(group, amount, portion, cost, item.quantity)
    return gross, discount, cost_total, quantity, estimated_count


def _sales_aggregates(sales, filters):
    gross = allocated_discount = sold_cost = Decimal('0')
    estimated_cost_lines = sold_quantity = sale_count = 0
    by_product = defaultdict(_empty_sales_group)
    by_category = defaultdict(_empty_sales_group)
    by_day = defaultdict(_empty_sales_group)
    for sale in sales:
        values = _accumulate_sale(sale, filters, by_product, by_category, by_day)
        if values is None:
            continue
        amount, discount, cost, quantity, estimated = values
        gross += amount
        allocated_discount += discount
        sold_cost += cost
        sold_quantity += quantity
        estimated_cost_lines += estimated
        sale_count += 1
    return {
        'gross': gross, 'discount': allocated_discount, 'cost': sold_cost,
        'estimated_lines': estimated_cost_lines, 'units': sold_quantity,
        'count': sale_count, 'products': by_product,
        'categories': by_category, 'days': by_day,
    }


def _formatted_sales_groups(aggregates):
    products = [
        {'id': key[0], 'name': key[1], 'category': key[2],
         'quantity': row['quantity'], 'gross': money(row['gross']),
         'discounts': money(row['discount']),
         'revenue': money(row['gross'] - row['discount']),
         'cogs': money(row['cost']),
         'gross_profit': money(row['gross'] - row['discount'] - row['cost'])}
        for key, row in aggregates['products'].items()
    ]
    categories = [
        {'name': name, 'quantity': row['quantity'],
         'revenue': money(row['gross'] - row['discount']),
         'cogs': money(row['cost']),
         'gross_profit': money(row['gross'] - row['discount'] - row['cost'])}
        for name, row in aggregates['categories'].items()
    ]
    days = [
        {'date': day, 'quantity': row['quantity'],
         'revenue': money(row['gross'] - row['discount']),
         'cogs': money(row['cost']),
         'gross_profit': money(row['gross'] - row['discount'] - row['cost'])}
        for day, row in sorted(aggregates['days'].items())
    ]
    return products, categories, days


def _purchase_records(begin, finish, filters):
    movements = (StockMovement.objects.filter(
        created_at__gte=begin, created_at__lt=finish,
        reason=StockMovement.Reason.ADJUSTMENT,
        justification=StockMovement.Justification.RECEIPT,
        delta__gt=0,
    ).select_related('product__category').order_by('-created_at', '-pk'))
    purchases = []
    purchase_total = Decimal('0')
    purchased_units = estimated_purchases = 0
    for receipt in movements:
        if 'product' in filters and receipt.product_id != filters['product']:
            continue
        if 'category' in filters and receipt.product.category_id != filters['category']:
            continue
        estimated = receipt.unit_cost is None
        unit_cost = receipt.product.purchase_price if estimated else receipt.unit_cost
        amount = unit_cost * receipt.delta
        purchase_total += amount
        purchased_units += receipt.delta
        estimated_purchases += int(estimated)
        purchases.append({
            'id': receipt.pk, 'date': timezone.localtime(receipt.created_at).date().isoformat(),
            'product': receipt.product.name, 'sku': receipt.product.sku,
            'quantity': receipt.delta, 'unit_cost': money(unit_cost),
            'total': money(amount), 'estimated': estimated,
        })
    return purchases, purchase_total, purchased_units, estimated_purchases


def _manual_financial_records(start, end, company_scope):
    if not company_scope:
        return [], [], Decimal('0'), Decimal('0')
    entries = FinancialEntry.objects.filter(
        entry_date__gte=start, entry_date__lte=end, voided_at__isnull=True
    ).order_by('-entry_date', '-pk')
    expenses, investments = [], []
    expense_total = capital_total = Decimal('0')
    for entry in entries:
        data = {'id': entry.pk, 'date': entry.entry_date.isoformat(),
                'kind': entry.kind, 'category': entry.get_category_display(),
                'description': entry.description, 'amount': money(entry.amount)}
        if entry.kind == FinancialEntry.Kind.EXPENSE:
            expenses.append(data)
            expense_total += entry.amount
        else:
            investments.append(data)
            capital_total += entry.amount
    return expenses, investments, expense_total, capital_total


def finance_report(filters):
    """Receita, CMV e despesas: custos de estoque não duplicam despesas."""
    start, end = filters['start'], filters['end']
    begin = timezone.make_aware(datetime.combine(start, time.min))
    finish = timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min))
    sales = (Sale.objects.filter(created_at__gte=begin, created_at__lt=finish,
                                 canceled_at__isnull=True)
             .prefetch_related('items__product__category').order_by('created_at', 'pk'))
    aggregate = _sales_aggregates(sales, filters)
    products, categories, days = _formatted_sales_groups(aggregate)
    purchases, purchase_total, purchased_units, estimated_purchases = _purchase_records(begin, finish, filters)
    company_scope = 'product' not in filters and 'category' not in filters
    expenses, investments, expense_total, capital_total = _manual_financial_records(start, end, company_scope)
    gross, discounts, sold_cost = aggregate['gross'], aggregate['discount'], aggregate['cost']
    sale_count = aggregate['count']
    revenue = gross - discounts
    gross_profit = revenue - sold_cost
    operating_result = gross_profit - expense_total if company_scope else None
    margin = gross_profit / revenue * 100 if revenue else Decimal('0')
    return {
        'filters': {'start': start.isoformat(), 'end': end.isoformat(),
                    'category': filters.get('category'), 'product': filters.get('product')},
        'summary': {'gross': money(gross), 'discounts': money(discounts),
                    'revenue': money(revenue), 'sales_count': sale_count,
                    'items_sold': aggregate['units'],
                    'average_ticket': money(revenue / sale_count) if sale_count else Decimal('0'),
                    'cogs': money(sold_cost), 'gross_profit': money(gross_profit),
                    'gross_margin_percentage': money(margin),
                    'expense_total': money(expense_total),
                    'operating_result': money(operating_result) if operating_result is not None else None,
                    'purchase_total': money(purchase_total), 'purchase_units': purchased_units,
                    'purchase_count': len(purchases), 'capital_investments': money(capital_total),
                    'registered_outlays': money(purchase_total + expense_total + capital_total),
                    'estimated_cost_lines': aggregate['estimated_lines'],
                    'estimated_purchase_entries': estimated_purchases,
                    'company_scope': company_scope},
        'products': sorted(products, key=lambda product: (-product['revenue'], product['name'])),
        'categories': sorted(categories, key=lambda category: (-category['revenue'], category['name'])),
        'daily': days,
        'purchases': purchases, 'expenses': expenses, 'investments': investments,
    }
