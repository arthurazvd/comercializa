"""Módulo de serviço para análise de risco de vencimento de produtos e lotes (US09).

Fornece cálculo de dias restantes, categorização por severidade, estimativa do
capital em risco financeiro e recomendações orientadas à decisão gerencial.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from django.utils import timezone
from .models import Product, StockLot

SEVERITY_EXPIRED = "vencido"
SEVERITY_CRITICAL = "critico"
SEVERITY_WARNING = "alerta"
SEVERITY_ATTENTION = "atencao"

SEVERITY_ACTIONS = {
    SEVERITY_EXPIRED: "Segregar e descartar/baixar do estoque; item impróprio para venda.",
    SEVERITY_CRITICAL: "Liquidação urgente com desconto de até 50% ou degustação/queima imediata.",
    SEVERITY_WARNING: "Aplicar desconto promocional de 20% e posicionar na frente da gôndola.",
    SEVERITY_ATTENTION: "Priorizar saída no PDV e suspender novos pedidos de compra deste item.",
}


def classify_severity(days_remaining: int, window_days: int = 30) -> Optional[str]:
    """Classifica a severidade do alerta com base nos dias restantes até o vencimento."""
    if days_remaining < 0:
        return SEVERITY_EXPIRED
    if days_remaining <= 7:
        return SEVERITY_CRITICAL
    if days_remaining <= 15:
        return SEVERITY_WARNING
    if days_remaining <= window_days:
        return SEVERITY_ATTENTION
    return None


def get_recommended_action(severity: str) -> str:
    """Retorna a ação recomendada para a respectiva faixa de severidade."""
    return SEVERITY_ACTIONS.get(
        severity,
        "Monitorar o estoque e acompanhar a velocidade de vendas."
    )


def build_alert_payload(
    product: Product,
    expiration_date: date,
    quantity: int,
    unit_cost: Decimal,
    reference_date: date,
    window_days: int,
    lot_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Gera o dicionário de alerta individual para um lote ou estoque legado."""
    if quantity <= 0:
        return None

    days_remaining = (expiration_date - reference_date).days
    severity = classify_severity(days_remaining, window_days)
    if not severity:
        return None

    unit_cost_val = Decimal(str(unit_cost or product.purchase_price or Decimal("0.00")))
    sale_price_val = Decimal(str(product.sale_price or Decimal("0.00")))
    cost_at_risk = (Decimal(quantity) * unit_cost_val).quantize(Decimal("0.01"))
    potential_revenue_loss = (Decimal(quantity) * sale_price_val).quantize(Decimal("0.01"))

    return {
        "product_id": product.id,
        "product_name": product.name,
        "sku": product.sku or "",
        "category_id": product.category_id,
        "category_name": product.category.name if product.category else "Sem Categoria",
        "lot_id": lot_id,
        "is_legacy_stock": lot_id is None,
        "expiration_date": expiration_date.isoformat(),
        "days_remaining": days_remaining,
        "severity": severity,
        "quantity_at_risk": quantity,
        "unit_cost": float(unit_cost_val),
        "sale_price": float(sale_price_val),
        "cost_at_risk": float(cost_at_risk),
        "potential_revenue_loss": float(potential_revenue_loss),
        "recommended_action": get_recommended_action(severity),
    }


def get_expiration_alerts(
    reference_date: Optional[date] = None,
    window_days: int = 30,
    severity_filter: Optional[str] = None,
    category_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Retorna o relatório completo de alertas e métricas de risco financeiro."""
    if reference_date is None:
        reference_date = timezone.now().date()

    products_qs = Product.objects.filter(active=True).select_related("category").prefetch_related("lots")
    if category_id:
        products_qs = products_qs.filter(category_id=category_id)

    raw_alerts: List[Dict[str, Any]] = []

    for product in products_qs:
        assigned_quantity = 0
        active_lots = [lot for lot in product.lots.all() if lot.quantity > 0]

        for lot in active_lots:
            assigned_quantity += lot.quantity
            if lot.expiration_date:
                alert = build_alert_payload(
                    product=product,
                    expiration_date=lot.expiration_date,
                    quantity=lot.quantity,
                    unit_cost=lot.unit_cost,
                    reference_date=reference_date,
                    window_days=window_days,
                    lot_id=lot.id,
                )
                if alert:
                    raw_alerts.append(alert)

        # Tratar saldo de estoque legado (sem lote registrado)
        legacy_stock = product.stock - assigned_quantity
        if legacy_stock > 0 and product.expiration_date:
            alert = build_alert_payload(
                product=product,
                expiration_date=product.expiration_date,
                quantity=legacy_stock,
                unit_cost=product.purchase_price,
                reference_date=reference_date,
                window_days=window_days,
                lot_id=None,
            )
            if alert:
                raw_alerts.append(alert)

    # Filtrar por severidade, se solicitado
    if severity_filter:
        norm_filter = severity_filter.strip().lower()
        filtered_alerts = [a for a in raw_alerts if a["severity"] == norm_filter]
    else:
        filtered_alerts = raw_alerts

    # Ordenar por criticidade (menor número de dias restantes primeiro)
    filtered_alerts.sort(key=lambda item: (item["days_remaining"], -item["cost_at_risk"]))

    # Compilar totais e sumário executivo
    total_quantity = sum((a["quantity_at_risk"] for a in filtered_alerts), 0)
    total_cost_risk = sum((Decimal(str(a["cost_at_risk"])) for a in filtered_alerts), Decimal("0.00"))
    total_rev_loss = sum((Decimal(str(a["potential_revenue_loss"])) for a in filtered_alerts), Decimal("0.00"))

    counts_by_severity = {
        SEVERITY_EXPIRED: sum(1 for a in raw_alerts if a["severity"] == SEVERITY_EXPIRED),
        SEVERITY_CRITICAL: sum(1 for a in raw_alerts if a["severity"] == SEVERITY_CRITICAL),
        SEVERITY_WARNING: sum(1 for a in raw_alerts if a["severity"] == SEVERITY_WARNING),
        SEVERITY_ATTENTION: sum(1 for a in raw_alerts if a["severity"] == SEVERITY_ATTENTION),
    }

    return {
        "reference_date": reference_date.isoformat(),
        "window_days": window_days,
        "summary": {
            "total_alerts": len(filtered_alerts),
            "total_items_at_risk": total_quantity,
            "total_cost_at_risk": float(total_cost_risk.quantize(Decimal("0.01"))),
            "total_potential_revenue_loss": float(total_rev_loss.quantize(Decimal("0.01"))),
            "counts_by_severity": counts_by_severity,
        },
        "alerts": filtered_alerts,
    }
