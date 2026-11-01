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


def finance_report(filters):
    """Alocação proporcional exata na base de dados, arredondamento apenas na saída."""
    start, end = filters['start'], filters['end']
    # Comparar data local; fim inclusivo. Evita erro em horários de última venda.
    # Intervalo sem cast de DATE na coluna: aproveita o índice de created_at.
    begin = timezone.make_aware(datetime.combine(start, time.min))
    finish = timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min))
    sales = (Sale.objects.filter(created_at__gte=begin, created_at__lt=finish,
                                  canceled_at__isnull=True)
             .prefetch_related('items__product__category').order_by('created_at', 'pk'))
    gross = Decimal('0')
    allocated_discount = Decimal('0')
    sold_cost = Decimal('0')
    estimated_cost_lines = 0
    sold_quantity = 0
    sale_count = 0
    by_product = defaultdict(lambda: {'quantity': 0, 'gross': Decimal('0'), 'discount': Decimal('0'), 'cost': Decimal('0')})
    by_category = defaultdict(lambda: {'quantity': 0, 'gross': Decimal('0'), 'discount': Decimal('0'), 'cost': Decimal('0')})
    by_day = defaultdict(lambda: {'gross': Decimal('0'), 'discount': Decimal('0'), 'quantity': 0, 'cost': Decimal('0')})
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
            # Custo congelado no PDV da V1.3.0. Registros anteriores sem
            # custo_total exigem estimativa explícita, nunca lucro afirmado
            # como custo histórico definitivo.
            if i.cost_total is None:
                cost = i.product.purchase_price * i.quantity
                estimated_cost_lines += 1
            else:
                cost = i.cost_total
            sold_cost += cost
            category = i.product.category.name if i.product.category_id else 'Sem categoria'
            product_key = (i.product_id, i.product.name, category)
            row = by_product[product_key]
            group = by_category[category]
            for target in (row, group, by_day[day]):
                target['gross'] += amount
                target['discount'] += portion
                target['cost'] += cost
                target['quantity'] += i.quantity
    products = [
        {'id': key[0], 'name': key[1], 'category': key[2],
         'quantity': v['quantity'], 'gross': money(v['gross']),
         'discounts': money(v['discount']), 'revenue': money(v['gross'] - v['discount']),
         'cogs': money(v['cost']), 'gross_profit': money(v['gross'] - v['discount'] - v['cost'])}
        for key, v in by_product.items()
    ]
    categories = [
        {'name': name, 'quantity': v['quantity'], 'revenue': money(v['gross'] - v['discount']),
         'cogs': money(v['cost']), 'gross_profit': money(v['gross'] - v['discount'] - v['cost'])}
        for name, v in by_category.items()
    ]
    days = [
        {'date': day, 'quantity': v['quantity'], 'revenue': money(v['gross'] - v['discount']),
         'cogs': money(v['cost']), 'gross_profit': money(v['gross'] - v['discount'] - v['cost'])}
        for day, v in sorted(by_day.items())
    ]
    revenue = gross - allocated_discount
    gross_profit = revenue - sold_cost

    # Compras reconhecidas pela movimentação de recebimento; compra de
    # mercadoria é formação de estoque, NÃO despesa operacional na mesma data.
    receipt_movements = (StockMovement.objects.filter(
        created_at__gte=begin, created_at__lt=finish,
        reason=StockMovement.Reason.ADJUSTMENT,
        justification=StockMovement.Justification.RECEIPT,
        delta__gt=0,
    ).select_related('product__category').order_by('-created_at', '-pk'))
    purchases = []
    purchase_total = Decimal('0')
    purchased_units = 0
    estimated_purchases = 0
    for receipt in receipt_movements:
        if ('product' in filters and receipt.product_id != filters['product']
                or 'category' in filters and receipt.product.category_id != filters['category']):
            continue
        # Recebimentos feitos antes da V1.3.0 não registravam preço unitário:
        # o custo de referência serve somente como estimativa informada.
        estimated = receipt.unit_cost is None
        unit_cost = receipt.unit_cost if not estimated else receipt.product.purchase_price
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

    # Gastos manuais pertencem à empresa toda, não a um SKU específico.
    # Não alocar 100% dos custos fixos a um único produto filtrado.
    company_scope = 'product' not in filters and 'category' not in filters
    manual = (FinancialEntry.objects.filter(
        entry_date__gte=start, entry_date__lte=end, voided_at__isnull=True
    ).order_by('-entry_date', '-pk')) if company_scope else FinancialEntry.objects.none()
    expenses, investments = [], []
    expense_total, capital_total = Decimal('0'), Decimal('0')
    for entry in manual:
        data = {'id': entry.pk, 'date': entry.entry_date.isoformat(),
                'kind': entry.kind, 'category': entry.get_category_display(),
                'description': entry.description, 'amount': money(entry.amount)}
        if entry.kind == FinancialEntry.Kind.EXPENSE:
            expenses.append(data)
            expense_total += entry.amount
        else:
            investments.append(data)
            capital_total += entry.amount
    operating_result = gross_profit - expense_total if company_scope else None
    margin = (gross_profit / revenue * 100) if revenue else Decimal('0')
    return {
        'filters': {'start': start.isoformat(), 'end': end.isoformat(),
                    'category': filters.get('category'), 'product': filters.get('product')},
        'summary': {'gross': money(gross), 'discounts': money(allocated_discount),
                    'revenue': money(revenue), 'sales_count': sale_count,
                    'items_sold': sold_quantity,
                    'average_ticket': money(revenue / sale_count) if sale_count else Decimal('0'),
                    'cogs': money(sold_cost), 'gross_profit': money(gross_profit),
                    'gross_margin_percentage': money(margin),
                    'expense_total': money(expense_total),
                    'operating_result': money(operating_result) if operating_result is not None else None,
                    'purchase_total': money(purchase_total), 'purchase_units': purchased_units,
                    'purchase_count': len(purchases), 'capital_investments': money(capital_total),
                    'registered_outlays': money(purchase_total + expense_total + capital_total),
                    'estimated_cost_lines': estimated_cost_lines,
                    'estimated_purchase_entries': estimated_purchases,
                    'company_scope': company_scope},
        'products': sorted(products, key=lambda p: (-p['revenue'], p['name'])),
        'categories': sorted(categories, key=lambda c: (-c['revenue'], c['name'])),
        'daily': days,
        'purchases': purchases, 'expenses': expenses, 'investments': investments,
    }
