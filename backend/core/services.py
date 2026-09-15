from datetime import timedelta
from decimal import Decimal
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from .models import Product, Sale, SaleItem


def dashboard_data():
    today = timezone.localdate()
    last_30_days = today - timedelta(days=30)
    expiration_limit = today + timedelta(days=15)

    sales_30 = Sale.objects.filter(created_at__date__gte=last_30_days)
    items_30 = SaleItem.objects.filter(sale__created_at__date__gte=last_30_days)

    revenue_expression = ExpressionWrapper(
        F("quantity") * F("unit_price"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )

    gross_revenue = items_30.aggregate(
        value=Coalesce(Sum(revenue_expression), Decimal("0"))
    )["value"]
    discounts = sales_30.aggregate(
        value=Coalesce(Sum("discount"), Decimal("0"))
    )["value"]
    revenue = max(gross_revenue - discounts, Decimal("0"))

    top_products = list(
        items_30.values("product_id", "product__name")
        .annotate(quantity_sold=Sum("quantity"))
        .order_by("-quantity_sold")[:5]
    )

    low_stock = Product.objects.filter(
        active=True, stock__lte=F("minimum_stock")
    ).order_by("stock")

    expiring = Product.objects.filter(
        active=True,
        expiration_date__isnull=False,
        expiration_date__gte=today,
        expiration_date__lte=expiration_limit,
    ).order_by("expiration_date")

    sold_ids = items_30.values_list("product_id", flat=True).distinct()
    stagnant = Product.objects.filter(active=True, stock__gt=0).exclude(id__in=sold_ids)[:10]

    velocity_rows = {
        row["product_id"]: row["qty"] / 30
        for row in items_30.values("product_id").annotate(qty=Sum("quantity"))
    }

    recommendations = []

    for product in Product.objects.filter(active=True):
        velocity = float(velocity_rows.get(product.id, 0))
        days_cover = (product.stock / velocity) if velocity > 0 else None

        if product.stock <= product.minimum_stock:
            suggested_qty = max(
                product.minimum_stock * 2 - product.stock,
                int(round(velocity * 15)) - product.stock,
                1,
            )
            priority = "alta" if product.stock == 0 or (days_cover is not None and days_cover <= 3) else "média"
            recommendations.append({
                "type": "reposição",
                "priority": priority,
                "product_id": product.id,
                "product": product.name,
                "message": f"Repor aproximadamente {suggested_qty} unidade(s).",
                "reason": "Estoque atual está no nível mínimo ou abaixo dele.",
            })

        if product.expiration_date:
            days_to_expire = (product.expiration_date - today).days
            if 0 <= days_to_expire <= 15 and product.stock > 0:
                priority = "alta" if days_to_expire <= 5 else "média"
                recommendations.append({
                    "type": "validade",
                    "priority": priority,
                    "product_id": product.id,
                    "product": product.name,
                    "message": "Avaliar promoção ou desconto para acelerar a saída.",
                    "reason": f"Produto vence em {days_to_expire} dia(s).",
                })

        if product.id not in sold_ids and product.stock > 0:
            recommendations.append({
                "type": "baixa movimentação",
                "priority": "baixa",
                "product_id": product.id,
                "product": product.name,
                "message": "Reavaliar nova compra e considerar ação promocional.",
                "reason": "Nenhuma venda registrada nos últimos 30 dias.",
            })

    priority_order = {"alta": 0, "média": 1, "baixa": 2}
    recommendations.sort(key=lambda x: priority_order[x["priority"]])

    return {
        "period_days": 30,
        "summary": {
            "revenue": revenue,
            "sales_count": sales_30.count(),
            "products_count": Product.objects.filter(active=True).count(),
            "low_stock_count": low_stock.count(),
            "expiring_count": expiring.count(),
        },
        "top_products": top_products,
        "low_stock": [
            {
                "id": p.id, "name": p.name, "stock": p.stock,
                "minimum_stock": p.minimum_stock
            } for p in low_stock[:10]
        ],
        "expiring": [
            {
                "id": p.id, "name": p.name, "stock": p.stock,
                "expiration_date": p.expiration_date
            } for p in expiring[:10]
        ],
        "stagnant": [
            {"id": p.id, "name": p.name, "stock": p.stock}
            for p in stagnant
        ],
        "recommendations": recommendations[:20],
    }
