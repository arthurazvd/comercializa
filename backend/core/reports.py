"""Consultas financeiras filtradas. Descontos são rateados entre itens da venda.

Receita líquida aqui significa *venda menos descontos*; não é lucro líquido.
"""
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Sale

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


def finance_report(filters):
    """Alocação proporcional exata na base de dados, arredondamento apenas na saída."""
    start, end = filters['start'], filters['end']
    # Comparar data local; fim inclusivo. Evita erro em horários de última venda.
    # Intervalo sem cast de DATE na coluna: aproveita o índice de created_at.
    begin = timezone.make_aware(datetime.combine(start, time.min))
    finish = timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min))
    sales = (Sale.objects.filter(created_at__gte=begin, created_at__lt=finish)
             .prefetch_related('items__product__category').order_by('created_at', 'pk'))
    gross = Decimal('0')
    allocated_discount = Decimal('0')
    sold_quantity = 0
    sale_count = 0
    by_product = defaultdict(lambda: {'quantity': 0, 'gross': Decimal('0'), 'discount': Decimal('0')})
    by_category = defaultdict(lambda: {'quantity': 0, 'gross': Decimal('0'), 'discount': Decimal('0')})
    by_day = defaultdict(lambda: {'gross': Decimal('0'), 'discount': Decimal('0'), 'quantity': 0})
    for sale in sales:
        items = list(sale.items.all())
        total_gross = sum((i.unit_price * i.quantity for i in items), Decimal('0'))
        selected = [i for i in items if
                    ('category' not in filters or i.product.category_id == filters['category'])
                    and ('product' not in filters or i.product_id == filters['product'])]
        if not selected:
            continue
        sale_count += 1
        day = timezone.localtime(sale.created_at).date().isoformat()
        for i in selected:
            amount = i.unit_price * i.quantity
            # Se total_gross == 0, descontos devem obrigatoriamente ser zero.
            portion = sale.discount * amount / total_gross if total_gross else Decimal('0')
            gross += amount
            allocated_discount += portion
            sold_quantity += i.quantity
            category = i.product.category.name if i.product.category_id else 'Sem categoria'
            product_key = (i.product_id, i.product.name, category)
            row = by_product[product_key]
            group = by_category[category]
            for target in (row, group, by_day[day]):
                target['gross'] += amount
                target['discount'] += portion
                target['quantity'] += i.quantity
    products = [
        {'id': key[0], 'name': key[1], 'category': key[2],
         'quantity': v['quantity'], 'gross': money(v['gross']),
         'discounts': money(v['discount']), 'revenue': money(v['gross'] - v['discount'])}
        for key, v in by_product.items()
    ]
    categories = [
        {'name': name, 'quantity': v['quantity'], 'revenue': money(v['gross'] - v['discount'])}
        for name, v in by_category.items()
    ]
    days = [
        {'date': day, 'quantity': v['quantity'], 'revenue': money(v['gross'] - v['discount'])}
        for day, v in sorted(by_day.items())
    ]
    revenue = gross - allocated_discount
    return {
        'filters': {'start': start.isoformat(), 'end': end.isoformat(),
                    'category': filters.get('category'), 'product': filters.get('product')},
        'summary': {'gross': money(gross), 'discounts': money(allocated_discount),
                    'revenue': money(revenue), 'sales_count': sale_count,
                    'items_sold': sold_quantity,
                    'average_ticket': money(revenue / sale_count) if sale_count else Decimal('0')},
        'products': sorted(products, key=lambda p: (-p['revenue'], p['name'])),
        'categories': sorted(categories, key=lambda c: (-c['revenue'], c['name'])),
        'daily': days,
    }
