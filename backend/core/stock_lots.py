"""Posição de saldo por lote e baixa FEFO (primeiro a vencer, primeiro a sair).

O saldo sem lote explícito é tratado como legado; sua validade é a do
cadastro do produto. Não altera retroativamente estoques já existentes.
"""
from datetime import date, timedelta
from django.db.models import F
from django.utils import timezone
from rest_framework import serializers


def stock_snapshot(product, today=None):
    today = today or timezone.localdate()
    lots = list(product.lots.all())
    tracked = sum(lot.quantity for lot in lots)
    legacy = max(0, product.stock - tracked)
    valid_legacy = legacy if not product.expiration_date or product.expiration_date >= today else 0
    available = valid_legacy + sum(lot.quantity for lot in lots if lot.expiration_date is None or lot.expiration_date >= today)
    expired = (legacy - valid_legacy) + sum(lot.quantity for lot in lots if lot.expiration_date is not None and lot.expiration_date < today)
    limit = today + timedelta(days=15)
    expiring = (legacy if product.expiration_date and today <= product.expiration_date <= limit else 0)
    expiring += sum(lot.quantity for lot in lots if lot.expiration_date is not None and today <= lot.expiration_date <= limit)
    dates = ([product.expiration_date] if legacy and product.expiration_date else []) + [lot.expiration_date for lot in lots if lot.quantity and lot.expiration_date]
    # Valor real: lotes por custo histórico, eventual saldo legado pelo custo
    # de referência. Não recalcular lotes antigos pelo preço da última compra.
    inventory_value = sum((lot.unit_cost * lot.quantity for lot in lots), product.purchase_price * legacy)
    expired_stock_value = (
        (product.purchase_price * (legacy - valid_legacy)) +
        sum((lot.unit_cost * lot.quantity for lot in lots
             if lot.expiration_date is not None and lot.expiration_date < today), product.purchase_price * 0)
    )
    return {
        'inventory_value': inventory_value, 'expired_stock_value': expired_stock_value,
        'available_stock': available, 'expired_units': expired, 'expiring_units': expiring,
        'nearest_expiration': min(dates) if dates else None,
        'lot_count': sum(1 for lot in lots if lot.quantity > 0),
    }


def consume_lots(product, quantity, *, sale_only):
    """Desconta saldos de lotes; executado dentro da transação do estoque.

    Retorna pares (lote, quantidade) para auditoria em StockLotAllocation.
    O saldo legado é implícito, não precisa ser atualizado separadamente.
    """
    today = timezone.localdate()
    # Validade NULL significa não perecível e deve sair por último no FEFO.
    lots = sorted(product.lots.select_for_update().all(),
                  key=lambda lot: (lot.expiration_date or date.max,
                                   0 if lot.receipt_movement_id is None else 1, lot.pk))
    tracked = sum(lot.quantity for lot in lots)
    legacy = max(0, product.stock - tracked)
    if sale_only:
        eligible_lots = [l for l in lots if l.expiration_date is None or l.expiration_date >= today]
        eligible_legacy = legacy if not product.expiration_date or product.expiration_date >= today else 0
        if quantity > eligible_legacy + sum(l.quantity for l in eligible_lots):
            raise serializers.ValidationError({'items': f"Estoque válido insuficiente para '{product.name}'."})
    else:
        eligible_lots = lots  # inclui avarias e descartes de itens vencidos
        eligible_legacy = legacy
    remaining = quantity
    consumed = []
    for lot in eligible_lots:
        amount = min(remaining, lot.quantity)
        if amount:
            if not type(lot).objects.filter(pk=lot.pk, quantity__gte=amount).update(quantity=F('quantity') - amount):
                raise serializers.ValidationError({'delta': 'Lote alterado simultaneamente. Tente novamente.'})
            consumed.append((lot, amount))
            remaining -= amount
        if remaining == 0:
            break
    if remaining > eligible_legacy:
        raise serializers.ValidationError({'delta': 'Saldo disponível insuficiente.'})
    return consumed


def seal_legacy_stock(product):
    """Congela o custo conhecido do saldo sem lote antes de trocar o custo-base."""
    tracked = sum(lot.quantity for lot in product.lots.select_for_update().all())
    legacy = max(0, product.stock - tracked)
    if legacy:
        from .models import StockLot
        StockLot.objects.create(
            product=product, expiration_date=product.expiration_date,
            received_quantity=legacy, quantity=legacy, unit_cost=product.purchase_price,
        )
    return legacy
