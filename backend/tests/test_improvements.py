"""Regressão da rodada de melhorias de estoque, vendas, validação e painel."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Product, Sale, StockMovement
from tests.factories import ProductFactory


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
class TestSalesIntegrity:
    def test_multiple_items_generate_auditable_movements(self, client):
        first = ProductFactory(stock=10, sale_price=Decimal("12.00"))
        second = ProductFactory(stock=4, sale_price=Decimal("5.00"))
        response = client.post("/api/sales/", {
            "items": [{"product": first.pk, "quantity": 3}, {"product": second.pk, "quantity": 2}],
            "discount": "2.00",
        }, format="json")
        assert response.status_code == 201, response.data
        assert Decimal(response.data["total"]) == Decimal("44.00")
        first.refresh_from_db()
        second.refresh_from_db()
        assert first.stock == 7 and second.stock == 2
        movements = list(StockMovement.objects.filter(sale_id=response.data["id"]).order_by("product_id"))
        assert len(movements) == 2
        assert {m.product_id: (m.delta, m.stock_before, m.stock_after) for m in movements} == {
            first.pk: (-3, 10, 7), second.pk: (-2, 4, 2),
        }
        first.sale_price = Decimal("99.00")
        first.save()
        assert Decimal(client.get("/api/sales/").data[0]["items"][0]["unit_price"]) == Decimal("12.00")

    @pytest.mark.parametrize("discount", ["-0.01", "100.01"])
    def test_rejects_invalid_discounts_without_writing(self, client, discount):
        product = ProductFactory(stock=8, sale_price=Decimal("10.00"))
        response = client.post("/api/sales/", {
            "items": [{"product": product.pk, "quantity": 1}], "discount": discount,
        }, format="json")
        assert response.status_code == 400
        product.refresh_from_db()
        assert product.stock == 8
        assert not Sale.objects.exists()
        assert not StockMovement.objects.exists()

    def test_rejects_expired_product_without_changing_stock(self, client):
        product = ProductFactory(stock=8, expiration_date=timezone.localdate() - timedelta(days=1))
        response = client.post("/api/sales/", {
            "items": [{"product": product.pk, "quantity": 2}],
        }, format="json")
        assert response.status_code == 400
        product.refresh_from_db()
        assert product.stock == 8

    def test_date_of_expiration_is_still_valid(self, client):
        product = ProductFactory(stock=8, expiration_date=timezone.localdate())
        response = client.post("/api/sales/", {
            "items": [{"product": product.pk, "quantity": 2}],
        }, format="json")
        assert response.status_code == 201

    def test_rejects_missing_product_and_duplicate_lines(self, client):
        product = ProductFactory(stock=8)
        for items in ([], [{"product": product.pk, "quantity": 1}] * 2):
            response = client.post("/api/sales/", {"items": items}, format="json")
            assert response.status_code == 400
        assert not Sale.objects.exists()


@pytest.mark.django_db
class TestStockIntegrity:
    def test_stock_entry_and_exit_with_audit(self, client):
        product = ProductFactory(stock=5)
        for delta, before, after in [(10, 5, 15), (-4, 15, 11)]:
            response = client.post("/api/stock-movements/", {
                "product": product.pk, "delta": delta, "note": "Inventário",
            }, format="json")
            assert response.status_code == 201, response.data
            assert response.data["stock_before"] == before
            assert response.data["stock_after"] == after
            assert response.data["reason"] == "adjustment"
        product.refresh_from_db()
        assert product.stock == 11
        assert len(client.get("/api/stock-movements/").data) == 2

    @pytest.mark.parametrize("delta,note", [(-6, "Inventário"), (0, "Inventário"), (2, "")])
    def test_rejects_invalid_adjustments(self, client, delta, note):
        product = ProductFactory(stock=5)
        response = client.post("/api/stock-movements/", {
            "product": product.pk, "delta": delta, "note": note,
        }, format="json")
        assert response.status_code == 400
        product.refresh_from_db()
        assert product.stock == 5
        assert not StockMovement.objects.exists()

    def test_corrections_via_product_editor_create_audit_event(self, client):
        product = ProductFactory(stock=5)
        response = client.patch(f"/api/products/{product.pk}/", {"stock": 8}, format="json")
        assert response.status_code == 200, response.data
        movement = StockMovement.objects.get(product=product)
        assert (movement.delta, movement.stock_before, movement.stock_after) == (3, 5, 8)
        assert movement.reason == StockMovement.Reason.ADJUSTMENT

    def test_deletion_with_stock_history_is_protected(self, client):
        product = ProductFactory(stock=2)
        client.post("/api/stock-movements/", {
            "product": product.pk, "delta": 1, "note": "Ajuste",
        }, format="json")
        response = client.delete(f"/api/products/{product.pk}/")
        assert response.status_code == 409
        assert Product.objects.filter(pk=product.pk).exists()

    def test_negative_product_prices_or_stock_are_invalid(self, client):
        for field in ("stock", "minimum_stock", "purchase_price", "sale_price"):
            product = ProductFactory()
            response = client.patch(f"/api/products/{product.pk}/", {field: -1}, format="json")
            assert response.status_code == 400


@pytest.mark.django_db
class TestDashboardImprovements:
    def test_daily_series_and_sales_indicators(self, client):
        product = ProductFactory(stock=10, sale_price=Decimal("20.00"))
        client.post("/api/sales/", {
            "discount": "5.00", "items": [{"product": product.pk, "quantity": 2}],
        }, format="json")
        response = client.get("/api/dashboard/")
        assert response.status_code == 200
        summary = response.data["summary"]
        assert Decimal(str(summary["revenue"])) == Decimal("35.00")
        assert Decimal(str(summary["gross_revenue"])) == Decimal("40.00")
        assert Decimal(str(summary["average_ticket"])) == Decimal("35.00")
        assert len(response.data["daily_revenue"]) == 7
        assert Decimal(str(response.data["daily_revenue"][-1]["revenue"])) == Decimal("35.00")

    def test_expired_inventory_is_reported_separately(self, client):
        ProductFactory(stock=3, expiration_date=timezone.localdate() - timedelta(days=2))
        ProductFactory(stock=3, expiration_date=timezone.localdate() + timedelta(days=2))
        response = client.get("/api/dashboard/")
        assert response.data["summary"]["expired_count"] == 1
        assert response.data["summary"]["expiring_count"] == 1
        assert any(r["type"] == "vencido" for r in response.data["recommendations"])
