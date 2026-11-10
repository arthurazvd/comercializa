"""Testes abrangentes para reports.py - cobre todas as ramificações (happy/sad paths)."""
import pytest
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from django.utils import timezone
from django.test import TestCase
from core.models import Product, Category, Sale, SaleItem, StockMovement, FinancialEntry
from tests.factories import CategoryFactory, ProductFactory, SaleFactory, SaleItemFactory
from core.reports import (
    filters_from_query, finance_report, _sales_aggregates, _formatted_sales_groups,
    _purchase_records, _manual_financial_records, money
)


@pytest.mark.django_db
class TestFiltersFromQuery:
    """Testes para filters_from_query (linhas 21-45) - cobre linha 75, 105, 160, 162"""

    def test_default_filters(self):
        """Filtros padrão: início do mês atual até hoje"""
        filters = filters_from_query({})
        today = timezone.localdate()
        assert filters['start'] == today.replace(day=1)
        assert filters['end'] == today
        assert 'category' not in filters
        assert 'product' not in filters

    def test_custom_start_end_dates(self):
        """Datas customizadas"""
        params = {'start': '2024-01-01', 'end': '2024-01-31'}
        filters = filters_from_query(params)
        assert filters['start'] == date(2024, 1, 1)
        assert filters['end'] == date(2024, 1, 31)

    def test_invalid_date_format(self):
        """Formato de data inválido deve levantar ValidationError (linha 28-29)"""
        params = {'start': '01-01-2024', 'end': '2024-01-31'}
        with pytest.raises(Exception) as exc:
            filters_from_query(params)
        assert 'datas válidas' in str(exc.value)

    def test_start_after_end(self):
        """Data inicial após final deve levantar ValidationError (linha 30-31)"""
        params = {'start': '2024-01-31', 'end': '2024-01-01'}
        with pytest.raises(Exception) as exc:
            filters_from_query(params)
        assert 'inicial não pode superar' in str(exc.value)

    def test_date_range_too_long(self):
        """Intervalo maior que 10 anos deve levantar ValidationError (linha 32-33)"""
        params = {'start': '2010-01-01', 'end': '2025-01-01'}
        with pytest.raises(Exception) as exc:
            filters_from_query(params)
        assert 'intervalo máximo' in str(exc.value)

    def test_valid_category_filter(self):
        """Filtro de categoria válido"""
        category = CategoryFactory()
        params = {'category': str(category.id)}
        filters = filters_from_query(params)
        assert filters['category'] == category.id

    def test_invalid_category_filter_zero(self):
        """Categoria ID zero deve levantar ValidationError (linha 40-41)"""
        params = {'category': '0'}
        with pytest.raises(Exception) as exc:
            filters_from_query(params)
        assert 'inteiro positivo' in str(exc.value)

    def test_invalid_category_filter_negative(self):
        """Categoria ID negativo deve levantar ValidationError"""
        params = {'category': '-1'}
        with pytest.raises(Exception) as exc:
            filters_from_query(params)
        assert 'inteiro positivo' in str(exc.value)

    def test_invalid_category_filter_non_numeric(self):
        """Categoria não numérica deve levantar ValidationError (linha 43-44)"""
        params = {'category': 'abc'}
        with pytest.raises(Exception) as exc:
            filters_from_query(params)
        assert 'inteiro positivo' in str(exc.value)

    def test_valid_product_filter(self):
        """Filtro de produto válido"""
        product = ProductFactory()
        params = {'product': str(product.id)}
        filters = filters_from_query(params)
        assert filters['product'] == product.id

    def test_invalid_product_filter_zero(self):
        """Produto ID zero deve levantar ValidationError"""
        params = {'product': '0'}
        with pytest.raises(Exception) as exc:
            filters_from_query(params)
        assert 'inteiro positivo' in str(exc.value)

    def test_both_category_and_product_filters(self):
        """Ambos os filtros"""
        category = CategoryFactory()
        product = ProductFactory(category=category)
        params = {'category': str(category.id), 'product': str(product.id)}
        filters = filters_from_query(params)
        assert filters['category'] == category.id
        assert filters['product'] == product.id


@pytest.mark.django_db
class TestSalesAggregates:
    """Testes para _sales_aggregates (linhas 96-118)"""

    def test_sales_aggregates_empty(self):
        """Sem vendas deve retornar zeros"""
        sales = Sale.objects.none()
        filters = {}
        result = _sales_aggregates(sales, filters)
        assert result['gross'] == Decimal('0')
        assert result['discount'] == Decimal('0')
        assert result['cost'] == Decimal('0')
        assert result['count'] == 0
        assert result['units'] == 0

    def test_sales_aggregates_with_sales(self):
        """Com vendas deve agregar corretamente"""
        category = CategoryFactory()
        product = ProductFactory(category=category, purchase_price=Decimal('10.00'))
        sale = SaleFactory(discount=Decimal('5.00'))
        SaleItemFactory(sale=sale, product=product, quantity=10, unit_price=Decimal('20.00'))

        sales = Sale.objects.filter(pk=sale.pk).prefetch_related('items__product__category')
        filters = {}
        result = _sales_aggregates(sales, filters)

        assert result['gross'] == Decimal('200.00')  # 10 * 20
        assert result['discount'] == Decimal('5.00')
        assert result['count'] == 1
        assert result['units'] == 10

    def test_sales_aggregates_filters_by_category(self):
        """Deve filtrar por categoria"""
        cat1 = CategoryFactory(name='Cat1')
        cat2 = CategoryFactory(name='Cat2')
        prod1 = ProductFactory(category=cat1, purchase_price=Decimal('10.00'))
        prod2 = ProductFactory(category=cat2, purchase_price=Decimal('10.00'))

        sale = SaleFactory()
        SaleItemFactory(sale=sale, product=prod1, quantity=5, unit_price=Decimal('20.00'))
        SaleItemFactory(sale=sale, product=prod2, quantity=5, unit_price=Decimal('20.00'))

        sales = Sale.objects.filter(pk=sale.pk).prefetch_related('items__product__category')
        filters = {'category': cat1.id}
        result = _sales_aggregates(sales, filters)

        assert result['gross'] == Decimal('100.00')  # Apenas prod1
        assert result['units'] == 5

    def test_sales_aggregates_filters_by_product(self):
        """Deve filtrar por produto"""
        product1 = ProductFactory(purchase_price=Decimal('10.00'))
        product2 = ProductFactory(purchase_price=Decimal('10.00'))

        sale = SaleFactory()
        SaleItemFactory(sale=sale, product=product1, quantity=5, unit_price=Decimal('20.00'))
        SaleItemFactory(sale=sale, product=product2, quantity=5, unit_price=Decimal('20.00'))

        sales = Sale.objects.filter(pk=sale.pk).prefetch_related('items__product__category')
        filters = {'product': product1.id}
        result = _sales_aggregates(sales, filters)

        assert result['gross'] == Decimal('100.00')
        assert result['units'] == 5

    def test_sales_aggregates_excludes_canceled_sales(self):
        """Deve excluir vendas canceladas"""
        product = ProductFactory(purchase_price=Decimal('10.00'))

        sale1 = SaleFactory()
        SaleItemFactory(sale=sale1, product=product, quantity=5, unit_price=Decimal('20.00'))

        sale2 = SaleFactory()
        sale2.canceled_at = timezone.now()
        sale2.save()
        SaleItemFactory(sale=sale2, product=product, quantity=5, unit_price=Decimal('20.00'))

        sales = Sale.objects.filter(canceled_at__isnull=True).prefetch_related('items__product__category')
        filters = {}
        result = _sales_aggregates(sales, filters)

        assert result['count'] == 1
        assert result['gross'] == Decimal('100.00')

    def test_sales_aggregates_discount_pro_rata(self):
        """Desconto deve ser rateado proporcionalmente"""
        product1 = ProductFactory(purchase_price=Decimal('10.00'))
        product2 = ProductFactory(purchase_price=Decimal('10.00'))

        sale = SaleFactory(discount=Decimal('10.00'))
        SaleItemFactory(sale=sale, product=product1, quantity=10, unit_price=Decimal('20.00'))  # 200
        SaleItemFactory(sale=sale, product=product2, quantity=10, unit_price=Decimal('10.00'))  # 100
        # Total bruto = 300, desconto = 10
        # product1: 200/300 * 10 = 6.67
        # product2: 100/300 * 10 = 3.33

        sales = Sale.objects.filter(pk=sale.pk).prefetch_related('items__product__category')
        filters = {}
        result = _sales_aggregates(sales, filters)

        assert result['discount'] == Decimal('10.00')
        # Verificar se o rateio está nas groups
        assert len(result['products']) == 2


@pytest.mark.django_db
class TestFormattedSalesGroups:
    """Testes para _formatted_sales_groups (linhas 121-145)"""

    def test_formatted_groups_structure(self):
        """Estrutura dos grupos formatados"""
        from collections import defaultdict

        def empty_group():
            return {'quantity': 0, 'gross': Decimal('0'), 'discount': Decimal('0'), 'cost': Decimal('0')}

        by_product = defaultdict(empty_group)
        by_category = defaultdict(empty_group)
        by_day = defaultdict(empty_group)

        product = ProductFactory()
        key = (product.id, product.name, 'Sem categoria')
        by_product[key] = {'quantity': 10, 'gross': Decimal('200.00'), 'discount': Decimal('5.00'), 'cost': Decimal('100.00')}
        by_category['Sem categoria'] = {'quantity': 10, 'gross': Decimal('200.00'), 'discount': Decimal('5.00'), 'cost': Decimal('100.00')}
        by_day['2024-01-15'] = {'quantity': 10, 'gross': Decimal('200.00'), 'discount': Decimal('5.00'), 'cost': Decimal('100.00')}

        products, categories, days = _formatted_sales_groups({
            'products': by_product, 'categories': by_category, 'days': by_day
        })

        assert len(products) == 1
        assert products[0]['quantity'] == 10
        assert products[0]['gross'] == Decimal('200.00')
        assert products[0]['revenue'] == Decimal('195.00')
        assert products[0]['cogs'] == Decimal('100.00')
        assert products[0]['gross_profit'] == Decimal('95.00')


@pytest.mark.django_db
class TestPurchaseRecords:
    """Testes para _purchase_records (linhas 148-175)"""

    def test_purchase_records_empty(self):
        """Sem recebimentos deve retornar vazio"""
        begin = timezone.make_aware(datetime.combine(date.today(), time.min))
        finish = timezone.make_aware(datetime.combine(date.today() + timedelta(days=1), time.min))
        filters = {}

        purchases, total, units, estimated = _purchase_records(begin, finish, filters)

        assert purchases == []
        assert total == Decimal('0')
        assert units == 0
        assert estimated == 0

    def test_purchase_records_with_receipt(self):
        """Com recebimento deve retornar dados"""
        product = ProductFactory(purchase_price=Decimal('10.00'))
        movement = StockMovement.objects.create(
            product=product,
            delta=50,
            stock_before=0,
            stock_after=50,
            reason='adjustment',
            justification='recebimento',
            unit_cost=Decimal('9.00'),
        )

        begin = timezone.make_aware(datetime.combine(date.today() - timedelta(days=1), time.min))
        finish = timezone.make_aware(datetime.combine(date.today() + timedelta(days=1), time.min))
        filters = {}

        purchases, total, units, estimated = _purchase_records(begin, finish, filters)

        assert len(purchases) == 1
        assert purchases[0]['product'] == product.name
        assert purchases[0]['quantity'] == 50
        assert purchases[0]['unit_cost'] == Decimal('9.00')
        assert purchases[0]['total'] == Decimal('450.00')
        assert purchases[0]['estimated'] is False
        assert total == Decimal('450.00')
        assert units == 50
        assert estimated == 0

    def test_purchase_records_estimated_cost(self):
        """Sem unit_cost deve usar purchase_price do produto e marcar estimated"""
        product = ProductFactory(purchase_price=Decimal('10.00'))
        movement = StockMovement.objects.create(
            product=product,
            delta=50,
            stock_before=0,
            stock_after=50,
            reason='adjustment',
            justification='recebimento',
            unit_cost=None,  # Estimado
        )

        begin = timezone.make_aware(datetime.combine(date.today() - timedelta(days=1), time.min))
        finish = timezone.make_aware(datetime.combine(date.today() + timedelta(days=1), time.min))
        filters = {}

        purchases, total, units, estimated = _purchase_records(begin, finish, filters)

        assert purchases[0]['estimated'] is True
        assert purchases[0]['unit_cost'] == Decimal('10.00')
        assert estimated == 1

    def test_purchase_records_filters_by_category(self):
        """Deve filtrar por categoria"""
        cat1 = CategoryFactory()
        cat2 = CategoryFactory()
        prod1 = ProductFactory(category=cat1, purchase_price=Decimal('10.00'))
        prod2 = ProductFactory(category=cat2, purchase_price=Decimal('10.00'))

        StockMovement.objects.create(product=prod1, delta=10, stock_before=0, stock_after=10, reason='adjustment', justification='recebimento')
        StockMovement.objects.create(product=prod2, delta=20, stock_before=0, stock_after=20, reason='adjustment', justification='recebimento')

        begin = timezone.make_aware(datetime.combine(date.today() - timedelta(days=1), time.min))
        finish = timezone.make_aware(datetime.combine(date.today() + timedelta(days=1), time.min))
        filters = {'category': cat1.id}

        purchases, total, units, estimated = _purchase_records(begin, finish, filters)

        assert len(purchases) == 1
        assert purchases[0]['product'] == prod1.name

    def test_purchase_records_filters_by_product(self):
        """Deve filtrar por produto"""
        product1 = ProductFactory(purchase_price=Decimal('10.00'))
        product2 = ProductFactory(purchase_price=Decimal('10.00'))

        StockMovement.objects.create(product=product1, delta=10, stock_before=0, stock_after=10, reason='adjustment', justification='recebimento')
        StockMovement.objects.create(product=product2, delta=20, stock_before=0, stock_after=20, reason='adjustment', justification='recebimento')

        begin = timezone.make_aware(datetime.combine(date.today() - timedelta(days=1), time.min))
        finish = timezone.make_aware(datetime.combine(date.today() + timedelta(days=1), time.min))
        filters = {'product': product1.id}

        purchases, total, units, estimated = _purchase_records(begin, finish, filters)

        assert len(purchases) == 1
        assert purchases[0]['product'] == product1.name


@pytest.mark.django_db
class TestManualFinancialRecords:
    """Testes para _manual_financial_records (linhas 178-196)"""

    def test_financial_records_empty(self):
        """Sem lançamentos deve retornar vazio"""
        start = date.today()
        end = date.today()
        company_scope = True

        expenses, investments, expense_total, capital_total = _manual_financial_records(start, end, company_scope)

        assert expenses == []
        assert investments == []
        assert expense_total == Decimal('0')
        assert capital_total == Decimal('0')

    def test_financial_records_with_expenses(self):
        """Com despesas"""
        FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel',
            amount=Decimal('1000.00'), entry_date=date.today()
        )

        start = date.today()
        end = date.today()
        company_scope = True

        expenses, investments, expense_total, capital_total = _manual_financial_records(start, end, company_scope)

        assert len(expenses) == 1
        assert expenses[0]['description'] == 'Aluguel'
        assert expense_total == Decimal('1000.00')
        assert capital_total == Decimal('0')

    def test_financial_records_with_investments(self):
        """Com investimentos"""
        FinancialEntry.objects.create(
            kind='investment', category='equipamentos', description='Notebook',
            amount=Decimal('5000.00'), entry_date=date.today()
        )

        start = date.today()
        end = date.today()
        company_scope = True

        expenses, investments, expense_total, capital_total = _manual_financial_records(start, end, company_scope)

        assert len(investments) == 1
        assert investments[0]['description'] == 'Notebook'
        assert expense_total == Decimal('0')
        assert capital_total == Decimal('5000.00')

    def test_financial_records_excludes_voided(self):
        """Deve excluir lançamentos anulados"""
        entry = FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel',
            amount=Decimal('1000.00'), entry_date=date.today()
        )
        entry.voided_at = timezone.now()
        entry.save()

        start = date.today()
        end = date.today()
        company_scope = True

        expenses, investments, expense_total, capital_total = _manual_financial_records(start, end, company_scope)

        assert len(expenses) == 0
        assert expense_total == Decimal('0')

    def test_financial_records_company_scope_false(self):
        """company_scope=False deve retornar vazio (linha 179-180)"""
        FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel',
            amount=Decimal('1000.00'), entry_date=date.today()
        )

        start = date.today()
        end = date.today()
        company_scope = False

        expenses, investments, expense_total, capital_total = _manual_financial_records(start, end, company_scope)

        assert expenses == []
        assert investments == []
        assert expense_total == Decimal('0')
        assert capital_total == Decimal('0')


@pytest.mark.django_db
class TestFinanceReport:
    """Testes para finance_report (linhas 199-239)"""

    def test_finance_report_basic(self):
        """Relatório financeiro básico"""
        category = CategoryFactory()
        product = ProductFactory(category=category, purchase_price=Decimal('10.00'))
        sale = SaleFactory(discount=Decimal('5.00'))
        SaleItemFactory(sale=sale, product=product, quantity=10, unit_price=Decimal('20.00'))

        filters = {'start': date.today().replace(day=1), 'end': date.today()}
        report = finance_report(filters)

        assert 'summary' in report
        assert report['summary']['gross'] == Decimal('200.00')
        assert report['summary']['discounts'] == Decimal('5.00')
        assert report['summary']['revenue'] == Decimal('195.00')
        assert report['summary']['cogs'] == Decimal('100.00')
        assert report['summary']['gross_profit'] == Decimal('95.00')

    def test_finance_report_with_expenses(self):
        """Relatório com despesas"""
        product = ProductFactory(purchase_price=Decimal('10.00'))
        sale = SaleFactory()  # discount = 0 por padrão
        SaleItemFactory(sale=sale, product=product, quantity=10, unit_price=Decimal('20.00'))

        FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel',
            amount=Decimal('1000.00'), entry_date=date.today()
        )

        filters = {'start': date.today().replace(day=1), 'end': date.today()}
        report = finance_report(filters)

        assert report['summary']['expense_total'] == Decimal('1000.00')
        # gross = 200, revenue = 200, cogs = 100, gross_profit = 100
        # operating_result = 100 - 1000 = -900
        assert report['summary']['operating_result'] == Decimal('-900.00')
        assert report['summary']['company_scope'] is True

    def test_finance_report_product_filter_no_operating_result(self):
        """Filtro por produto não deve calcular operating_result (linha 216)"""
        product = ProductFactory(purchase_price=Decimal('10.00'))
        sale = SaleFactory()
        SaleItemFactory(sale=sale, product=product, quantity=10, unit_price=Decimal('20.00'))

        FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel',
            amount=Decimal('1000.00'), entry_date=date.today()
        )

        filters = {'start': date.today().replace(day=1), 'end': date.today(), 'product': product.id}
        report = finance_report(filters)

        assert report['summary']['company_scope'] is False
        assert report['summary']['operating_result'] is None
        # expense_total ainda é Decimal (0.00) pois não há company_scope
        assert report['summary']['expense_total'] == Decimal('0.00')

    def test_finance_report_category_filter_no_operating_result(self):
        """Filtro por categoria não deve calcular operating_result"""
        category = CategoryFactory()
        product = ProductFactory(category=category, purchase_price=Decimal('10.00'))
        sale = SaleFactory()
        SaleItemFactory(sale=sale, product=product, quantity=10, unit_price=Decimal('20.00'))

        filters = {'start': date.today().replace(day=1), 'end': date.today(), 'category': category.id}
        report = finance_report(filters)

        assert report['summary']['company_scope'] is False
        assert report['summary']['operating_result'] is None

    def test_finance_report_calculates_margin_percentage(self):
        """Deve calcular margem percentual"""
        product = ProductFactory(purchase_price=Decimal('10.00'))
        sale = SaleFactory()
        SaleItemFactory(sale=sale, product=product, quantity=10, unit_price=Decimal('20.00'))

        filters = {'start': date.today().replace(day=1), 'end': date.today()}
        report = finance_report(filters)

        # gross_profit = 100, revenue = 200, margin = 50%
        assert report['summary']['gross_margin_percentage'] == Decimal('50.00')

    def test_finance_report_zero_revenue_margin(self):
        """Margem com receita zero deve ser 0"""
        filters = {'start': date.today().replace(day=1), 'end': date.today()}
        report = finance_report(filters)

        assert report['summary']['gross_margin_percentage'] == Decimal('0.00')


@pytest.mark.django_db
class TestMoneyFunction:
    """Testes para função money (linha 17-18)"""

    def test_money_quantizes_decimal(self):
        """Deve quantizar para 2 casas decimais"""
        assert money(Decimal('10.123')) == Decimal('10.12')
        assert money(Decimal('10.125')) == Decimal('10.13')  # ROUND_HALF_UP
        assert money(Decimal('10.126')) == Decimal('10.13')

    def test_money_handles_integers(self):
        """Deve lidar com inteiros"""
        assert money(Decimal('10')) == Decimal('10.00')