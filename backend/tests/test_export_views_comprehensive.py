"""Testes abrangentes para export_views.py - cobre todas as ramificações (happy/sad paths)."""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import Product, Category, StockMovement, FinancialEntry
from tests.factories import CategoryFactory, ProductFactory, SaleFactory, SaleItemFactory
from core.export_views import stock_status, stock_data, excel_response
from core.stock_lots import stock_snapshot


@pytest.mark.django_db
class TestStockStatus:
    """Testes para stock_status (linha 18-28) - cobre linha 21 (inativo/normal/vencido/a_vencer/critico)"""

    def test_stock_status_inactive_product(self):
        """Produto inativo deve retornar 'inativo'"""
        product = ProductFactory(active=False, stock=10)
        today = timezone.localdate()
        snapshot = stock_snapshot(product, today)
        status = stock_status(product, today, snapshot)
        assert status == 'inativo'

    def test_stock_status_expired(self):
        """Produto com unidades vencidas deve retornar 'vencido'"""
        product = ProductFactory(active=True, stock=10, expiration_date=timezone.localdate() - timedelta(days=5))
        today = timezone.localdate()
        snapshot = stock_snapshot(product, today)
        status = stock_status(product, today, snapshot)
        assert status == 'vencido'

    def test_stock_status_expiring(self):
        """Produto com unidades a vencer deve retornar 'a_vencer'"""
        product = ProductFactory(active=True, stock=10, expiration_date=timezone.localdate() + timedelta(days=5))
        today = timezone.localdate()
        snapshot = stock_snapshot(product, today)
        status = stock_status(product, today, snapshot)
        assert status == 'a_vencer'

    def test_stock_status_critical_low_stock(self):
        """Produto com estoque abaixo do mínimo deve retornar 'critico'"""
        product = ProductFactory(active=True, stock=3, minimum_stock=5, expiration_date=None)
        today = timezone.localdate()
        snapshot = stock_snapshot(product, today)
        status = stock_status(product, today, snapshot)
        assert status == 'critico'

    def test_stock_status_normal(self):
        """Produto normal deve retornar 'normal'"""
        product = ProductFactory(active=True, stock=50, minimum_stock=5, expiration_date=None)
        today = timezone.localdate()
        snapshot = stock_snapshot(product, today)
        status = stock_status(product, today, snapshot)
        assert status == 'normal'

    def test_stock_status_exact_minimum(self):
        """Produto com estoque exatamente no mínimo deve retornar 'critico'"""
        product = ProductFactory(active=True, stock=5, minimum_stock=5, expiration_date=None)
        today = timezone.localdate()
        snapshot = stock_snapshot(product, today)
        status = stock_status(product, today, snapshot)
        assert status == 'critico'

    def test_stock_status_expiring_takes_priority_over_low_stock(self):
        """Validade a vencer deve ter prioridade sobre estoque baixo"""
        product = ProductFactory(active=True, stock=3, minimum_stock=5, expiration_date=timezone.localdate() + timedelta(days=5))
        today = timezone.localdate()
        snapshot = stock_snapshot(product, today)
        status = stock_status(product, today, snapshot)
        assert status == 'a_vencer'

    def test_stock_status_expired_takes_priority_over_expiring(self):
        """Validade vencida deve ter prioridade sobre a vencer"""
        product = ProductFactory(active=True, stock=10, expiration_date=timezone.localdate() - timedelta(days=1))
        today = timezone.localdate()
        snapshot = stock_snapshot(product, today)
        status = stock_status(product, today, snapshot)
        assert status == 'vencido'

    def test_stock_status_inactive_takes_priority(self):
        """Inativo deve ter prioridade sobre tudo"""
        product = ProductFactory(active=False, stock=0, minimum_stock=5, expiration_date=timezone.localdate() - timedelta(days=1))
        today = timezone.localdate()
        snapshot = stock_snapshot(product, today)
        status = stock_status(product, today, snapshot)
        assert status == 'inativo'


@pytest.mark.django_db
class TestStockData:
    """Testes para stock_data (linhas 31-58)"""

    def test_stock_data_empty(self):
        """stock_data sem produtos deve retornar estrutura vazia"""
        Product.objects.all().delete()
        data = stock_data()
        assert data['summary']['products'] == 0
        assert data['summary']['units'] == 0
        assert data['summary']['inventory_value'] == 0
        assert data['items'] == []

    def test_stock_data_with_products(self):
        """stock_data com produtos deve retornar todos os campos"""
        category = CategoryFactory()
        product = ProductFactory(category=category, stock=10, sale_price=Decimal('20.00'), purchase_price=Decimal('10.00'))
        data = stock_data()
        assert data['summary']['products'] == 1
        assert data['summary']['units'] == 10
        assert len(data['items']) == 1
        item = data['items'][0]
        assert item['id'] == product.id
        assert item['name'] == product.name
        assert item['sku'] == product.sku
        assert item['category'] == category.name
        assert item['stock'] == 10
        assert item['minimum_stock'] == product.minimum_stock
        assert item['unit_cost'] == product.purchase_price
        assert 'stock_value' in item
        assert 'average_cost' in item
        assert 'expired_stock_value' in item
        assert 'expiration_date' in item
        assert 'active' in item
        assert 'available_stock' in item
        assert 'expired_units' in item
        assert 'expiring_units' in item
        assert 'lot_count' in item
        assert 'status' in item
        assert 'low_stock' in item
        assert 'expired' in item
        assert 'expiring' in item

    def test_stock_data_inactive_product_excluded_from_summary(self):
        """Produtos inativos devem aparecer em items mas não no summary"""
        ProductFactory(active=True, stock=10)
        ProductFactory(active=False, stock=20)
        data = stock_data()
        assert data['summary']['products'] == 1
        assert data['summary']['units'] == 10
        assert len(data['items']) == 2
        assert any(item['active'] is False for item in data['items'])

    def test_stock_data_without_category(self):
        """Produto sem categoria deve mostrar 'Sem categoria'"""
        product = ProductFactory(category=None, stock=10)
        data = stock_data()
        assert data['items'][0]['category'] == 'Sem categoria'

    def test_stock_data_summary_calculations(self):
        """Verificar cálculos do summary"""
        ProductFactory(stock=10, purchase_price=Decimal('10.00'))
        ProductFactory(stock=20, purchase_price=Decimal('15.00'))
        data = stock_data()
        # inventory_value = 10*10 + 20*15 = 100 + 300 = 400
        assert data['summary']['inventory_value'] == 400
        assert data['summary']['units'] == 30
        assert data['summary']['products'] == 2


@pytest.mark.django_db
class TestStockExportView:
    """Testes para StockExportView (linhas 72-89)"""

    def test_stock_export_returns_xlsx(self):
        client = APIClient()
        ProductFactory(stock=10)
        response = client.get("/api/stock-export/")
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert 'comercializa_estoque.xlsx' in response['Content-Disposition']

    def test_stock_export_content_structure(self):
        client = APIClient()
        category = CategoryFactory(name='Test Category')
        product = ProductFactory(category=category, stock=10, sku='TEST-001', sale_price=Decimal('20.00'), purchase_price=Decimal('10.00'))
        response = client.get("/api/stock-export/")
        assert response.status_code == 200
        # Verificar que é um arquivo zip válido (xlsx)
        assert response.content[:4] == b'PK\x03\x04'  # ZIP signature

    def test_stock_export_with_multiple_products(self):
        client = APIClient()
        ProductFactory.create_batch(5)
        response = client.get("/api/stock-export/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestFinanceReportView:
    """Testes para FinanceReportView (linhas 92-95)"""

    def test_finance_report_returns_data(self):
        client = APIClient()
        response = client.get("/api/reports/finance/")
        assert response.status_code == 200
        assert 'summary' in response.data
        assert 'products' in response.data
        assert 'categories' in response.data
        assert 'daily' in response.data
        assert 'purchases' in response.data
        assert 'expenses' in response.data
        assert 'investments' in response.data

    def test_finance_report_with_filters(self):
        client = APIClient()
        category = CategoryFactory()
        product = ProductFactory(category=category)
        response = client.get("/api/reports/finance/?category=" + str(category.id))
        assert response.status_code == 200

    def test_finance_report_with_product_filter(self):
        client = APIClient()
        product = ProductFactory()
        response = client.get("/api/reports/finance/?product=" + str(product.id))
        assert response.status_code == 200

    def test_finance_report_with_date_range(self):
        client = APIClient()
        today = timezone.localdate()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()
        response = client.get(f"/api/reports/finance/?start={start}&end={end}")
        assert response.status_code == 200


@pytest.mark.django_db
class TestFinanceExportView:
    """Testes para FinanceExportView (linhas 98-144)"""

    def test_finance_export_returns_xlsx(self):
        client = APIClient()
        response = client.get("/api/reports/finance/export/")
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert 'comercializa_financeiro.xlsx' in response['Content-Disposition']

    def test_finance_export_content_structure(self):
        client = APIClient()
        response = client.get("/api/reports/finance/export/")
        assert response.status_code == 200
        assert response.content[:4] == b'PK\x03\x04'  # ZIP signature

    def test_finance_export_with_data(self):
        client = APIClient()
        category = CategoryFactory()
        product = ProductFactory(category=category, stock=10)
        SaleFactory()
        response = client.get("/api/reports/finance/export/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestExcelResponse:
    """Testes para excel_response (linhas 61-64)"""

    def test_excel_response_headers(self):
        from django.http import HttpResponse
        response = excel_response(b'test content', 'test.xlsx')
        assert isinstance(response, HttpResponse)
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert 'attachment; filename="test.xlsx"' in response['Content-Disposition']