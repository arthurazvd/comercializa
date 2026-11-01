from .stock_lots import stock_snapshot
from datetime import timedelta
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from .models import Product, Sale, SaleItem


def calculate_revenue(gross_revenue, discounts):
    """Calcula o faturamento líquido sem permitir valor negativo."""
    return max(gross_revenue - discounts, Decimal("0"))


def calculate_restock_quantity(stock, minimum_stock, velocity):
    """Calcula a quantidade sugerida para reposição de estoque."""
    return max(
        minimum_stock * 2 - stock,
        int(round(velocity * 15)) - stock,
        1,
    )


def dashboard_data():
    today = timezone.localdate()
    last_30_days = timezone.now() - timedelta(days=30)
    expiration_limit = today + timedelta(days=15)

    sales_30 = Sale.objects.filter(created_at__gte=last_30_days, canceled_at__isnull=True)
    items_30 = SaleItem.objects.filter(sale__created_at__gte=last_30_days,
                                       sale__canceled_at__isnull=True)

    revenue_expression = ExpressionWrapper(
        F("quantity") * F("unit_price"),
        output_field=DecimalField(
            max_digits=14,
            decimal_places=2,
        ),
    )

    gross_revenue = items_30.aggregate(
        value=Coalesce(
            Sum(revenue_expression),
            Decimal("0"),
        )
    )["value"]

    discounts = sales_30.aggregate(
        value=Coalesce(
            Sum("discount"),
            Decimal("0"),
        )
    )["value"]

    revenue = calculate_revenue(
        gross_revenue,
        discounts,
    )

    top_products = list(
        items_30.values(
            "product_id",
            "product__name",
        )
        .annotate(quantity_sold=Sum("quantity"))
        .order_by("-quantity_sold")[:5]
    )

    active_products = list(Product.objects.filter(active=True).prefetch_related('lots'))
    snapshots = {p.pk: stock_snapshot(p, today) for p in active_products}
    low_stock = [p for p in active_products if snapshots[p.pk]['available_stock'] <= p.minimum_stock]
    low_stock.sort(key=lambda p: snapshots[p.pk]['available_stock'])

    all_active = [p for p in active_products if p.stock > 0]
    expired = [p for p in all_active if snapshots[p.pk]['expired_units'] > 0]
    expiring = [p for p in all_active if snapshots[p.pk]['expiring_units'] > 0]
    expired.sort(key=lambda p: snapshots[p.pk]['nearest_expiration'] or today)
    expiring.sort(key=lambda p: snapshots[p.pk]['nearest_expiration'] or today)

    sold_ids = set(items_30.values_list("product_id", flat=True).distinct())

    stagnant = (
        Product.objects.filter(
            active=True,
            stock__gt=0,
        )
        .exclude(id__in=sold_ids)[:10]
    )

    velocity_rows = {
        row["product_id"]: row["qty"] / 30
        for row in items_30.values(
            "product_id"
        ).annotate(qty=Sum("quantity"))
    }

    # Série diária: as datas e os descontos usam o fuso configurado.
    chart_dates = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    daily_gross = {
        row["day"]: row["value"]
        for row in items_30.filter(sale__created_at__date__gte=chart_dates[0])
        .annotate(day=TruncDate("sale__created_at"))
        .values("day")
        .annotate(value=Sum(revenue_expression))
    }
    daily_discounts = {
        row["day"]: row["value"]
        for row in sales_30.filter(created_at__date__gte=chart_dates[0])
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(value=Sum("discount"))
    }
    daily_revenue = [
        {
            "date": day.isoformat(),
            "revenue": calculate_revenue(
                daily_gross.get(day, Decimal("0")),
                daily_discounts.get(day, Decimal("0")),
            ),
        }
        for day in chart_dates
    ]

    recommendations = []

    for product in active_products:
        velocity = float(
            velocity_rows.get(product.id, 0)
        )

        days_cover = (
            snapshots[product.pk]["available_stock"] / velocity
            if velocity > 0
            else None
        )

        if snapshots[product.pk]["available_stock"] <= product.minimum_stock:
            suggested_qty = calculate_restock_quantity(
                snapshots[product.pk]["available_stock"],
                product.minimum_stock,
                velocity,
            )

            priority = (
                "alta"
                if snapshots[product.pk]["available_stock"] == 0
                or (
                    days_cover is not None
                    and days_cover <= 3
                )
                else "média"
            )

            recommendations.append(
                {
                    "type": "reposição",
                    "priority": priority,
                    "product_id": product.id,
                    "product": product.name,
                    "message": (
                        f"Repor aproximadamente "
                        f"{suggested_qty} unidade(s)."
                    ),
                    "reason": (
                        "Estoque atual está no nível "
                        "mínimo ou abaixo dele."
                    ),
                }
            )

        product_snapshot = snapshots[product.pk]
        if product_snapshot["expired_units"] > 0:
            recommendations.append({
                "type": "vencido", "priority": "alta",
                "product_id": product.id, "product": product.name,
                "message": "Separar unidades vencidas; vender apenas o saldo válido.",
                "reason": "Validade já ultrapassada.",
            })

        if product_snapshot["expiring_units"]:
            valid_dates = [l.expiration_date for l in product.lots.all()
                           if l.quantity and today <= l.expiration_date <= expiration_limit]
            legacy_qty = product.stock - sum(l.quantity for l in product.lots.all())
            if legacy_qty > 0 and product.expiration_date and today <= product.expiration_date <= expiration_limit:
                valid_dates.append(product.expiration_date)
            days_to_expire = (min(valid_dates) - today).days if valid_dates else 16

            if (
                0 <= days_to_expire <= 15
                and product.stock > 0
            ):
                priority = (
                    "alta"
                    if days_to_expire <= 5
                    else "média"
                )

                recommendations.append(
                    {
                        "type": "validade",
                        "priority": priority,
                        "product_id": product.id,
                        "product": product.name,
                        "message": (
                            "Avaliar promoção ou desconto "
                            "para acelerar a saída."
                        ),
                        "reason": (
                            f"Produto vence em "
                            f"{days_to_expire} dia(s)."
                        ),
                    }
                )

        if (
            product.id not in sold_ids
            and product.stock > 0
        ):
            recommendations.append(
                {
                    "type": "baixa movimentação",
                    "priority": "baixa",
                    "product_id": product.id,
                    "product": product.name,
                    "message": (
                        "Reavaliar nova compra e considerar "
                        "ação promocional."
                    ),
                    "reason": (
                        "Nenhuma venda registrada nos "
                        "últimos 30 dias."
                    ),
                }
            )

    sales_count = sales_30.count()
    priority_order = {
        "alta": 0,
        "média": 1,
        "baixa": 2,
    }

    recommendations.sort(
        key=lambda x: priority_order[x["priority"]]
    )

    return {
        "period_days": 30,
        "summary": {
            "revenue": revenue,
            "gross_revenue": gross_revenue,
            "discounts": discounts,
            "average_ticket": revenue / sales_count if sales_count else Decimal("0"),
            "sales_count": sales_count,
            "products_count": len(active_products),
            "low_stock_count": len(low_stock),
            "expiring_count": len(expiring),
            "expired_count": len(expired),
        },
        "top_products": top_products,
        "daily_revenue": daily_revenue,
        "expired": [
            {"id": p.id, "name": p.name, "stock": p.stock, "expiration_date": snapshots[p.pk]["nearest_expiration"]}
            for p in expired[:10]
        ],
        "low_stock": [
            {
                "id": product.id,
                "name": product.name,
                "stock": product.stock,
                "available_stock": snapshots[product.pk]["available_stock"],
                "minimum_stock": product.minimum_stock,
            }
            for product in low_stock[:10]
        ],
        "expiring": [
            {
                "id": product.id,
                "name": product.name,
                "stock": product.stock,
                "expiration_date": snapshots[product.pk]["nearest_expiration"],
            }
            for product in expiring[:10]
        ],
        "stagnant": [
            {
                "id": product.id,
                "name": product.name,
                "stock": product.stock,
            }
            for product in stagnant
        ],
        "recommendations": recommendations[:20],
    }
