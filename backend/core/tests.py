from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from .models import Category, Product, Sale


class ComercializaAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        category = Category.objects.create(name="Alimentos")
        self.product = Product.objects.create(
            name="Arroz",
            category=category,
            sale_price="10.00",
            purchase_price="7.00",
            stock=10,
            minimum_stock=3,
        )

    def test_create_product(self):
        response = self.client.post("/api/products/", {
            "name": "Feijão",
            "sale_price": "8.00",
            "purchase_price": "5.00",
            "stock": 5,
            "minimum_stock": 2,
            "active": True,
        }, format="json")
        self.assertEqual(response.status_code, 201)

    def test_sale_reduces_stock(self):
        response = self.client.post("/api/sales/", {
            "discount": "0.00",
            "items": [{"product": self.product.id, "quantity": 2}],
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

    def test_sale_rejects_insufficient_stock(self):
        response = self.client.post("/api/sales/", {
            "items": [{"product": self.product.id, "quantity": 99}],
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_dashboard_marks_low_stock(self):
        self.product.stock = 2
        self.product.save()
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["low_stock_count"], 1)

    def test_dashboard_expiration_recommendation(self):
        self.product.expiration_date = timezone.localdate() + timedelta(days=3)
        self.product.save()
        response = self.client.get("/api/dashboard/")
        types = [item["type"] for item in response.data["recommendations"]]
        self.assertIn("validade", types)
