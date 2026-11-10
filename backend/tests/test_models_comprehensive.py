"""Testes abrangentes para models.py - cobre __str__ methods (linhas 61, 138, 156, 220)"""
import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from core.models import Category, Product, Sale, SaleItem, StockMovement, StockLot, FinancialEntry, StockLotAllocation
from tests.factories import CategoryFactory, ProductFactory, SaleFactory, SaleItemFactory
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestProductStr:
    """Teste para Product.__str__ (linha 44-45, coverage mostra linha 61)"""

    def test_product_str_returns_name(self):
        """__str__ deve retornar o nome do produto"""
        product = ProductFactory(name='Arroz Integral')
        assert str(product) == 'Arroz Integral'

    def test_product_str_with_special_chars(self):
        """__str__ com caracteres especiais"""
        product = ProductFactory(name='Pão de Queijo')
        assert str(product) == 'Pão de Queijo'

    def test_product_str_empty_name(self):
        """__str__ com nome vazio (embora validação impeça)"""
        product = ProductFactory(name='')
        assert str(product) == ''


@pytest.mark.django_db
class TestCategoryStr:
    """Teste para Category.__str__ (linha 13-14)"""

    def test_category_str_returns_name(self):
        """__str__ deve retornar o nome da categoria"""
        category = CategoryFactory(name='Alimentos')
        assert str(category) == 'Alimentos'


@pytest.mark.django_db
class TestSaleStr:
    """Teste para Sale.__str__ (linha 85-86, coverage mostra linha 138)"""

    def test_sale_str_format(self):
        """__str__ deve retornar 'Venda #PK'"""
        sale = SaleFactory()
        assert str(sale) == f'Venda #{sale.pk}'

    def test_sale_str_after_save(self):
        """__str__ após salvar deve ter PK"""
        sale = Sale.objects.create(discount=Decimal('5.00'))
        assert str(sale) == f'Venda #{sale.pk}'


@pytest.mark.django_db
class TestSaleItemStr:
    """SaleItem não tem __str__ próprio, usa padrão do Django"""


@pytest.mark.django_db
class TestStockMovementStr:
    """Teste para StockMovement.__str__ (linha 137-138, coverage mostra linha 156)"""

    def test_stock_movement_str_format(self):
        """__str__ deve retornar 'Produto: +delta (Motivo)'"""
        product = ProductFactory(name='Teste Produto')
        movement = StockMovement.objects.create(
            product=product,
            delta=10,
            stock_before=5,
            stock_after=15,
            reason='adjustment',
            justification='recebimento',
        )
        expected = f'{product}: +10 (Ajuste manual)'
        assert str(movement) == expected

    def test_stock_movement_str_negative_delta(self):
        """__str__ com delta negativo (venda)"""
        product = ProductFactory(name='Teste Produto')
        movement = StockMovement.objects.create(
            product=product,
            delta=-5,
            stock_before=15,
            stock_after=10,
            reason='sale',
        )
        expected = f'{product}: -5 (Venda)'
        assert str(movement) == expected

    def test_stock_movement_str_reversal(self):
        """__str__ para estorno"""
        product = ProductFactory(name='Teste Produto')
        movement = StockMovement.objects.create(
            product=product,
            delta=5,
            stock_before=10,
            stock_after=15,
            reason='reversal',
        )
        expected = f'{product}: +5 (Estorno de venda)'
        assert str(movement) == expected

    def test_stock_movement_str_all_justifications(self):
        """Testar todas as justificativas"""
        product = ProductFactory(name='Teste')
        for justification in ['recebimento', 'devolucao', 'avaria', 'perda', 'inventario', 'outro']:
            movement = StockMovement.objects.create(
                product=product,
                delta=1,
                stock_before=0,
                stock_after=1,
                reason='adjustment',
                justification=justification,
            )
            assert str(movement) == f'{product}: +1 (Ajuste manual)'


@pytest.mark.django_db
class TestStockLotStr:
    """Teste para StockLot.__str__ (linha 155-156, coverage mostra linha 220)"""

    def test_stock_lot_str_with_expiration(self):
        """__str__ com data de validade"""
        product = ProductFactory(name='Produto Teste')
        lot = StockLot.objects.create(
            product=product,
            expiration_date=timezone.localdate() + timedelta(days=30),
            received_quantity=100,
            quantity=50,
            unit_cost=Decimal('10.00'),
        )
        expected = f'{product.name} — {lot.expiration_date} (50)'
        assert str(lot) == expected

    def test_stock_lot_str_without_expiration(self):
        """__str__ sem data de validade (sem validade)"""
        product = ProductFactory(name='Produto Teste')
        lot = StockLot.objects.create(
            product=product,
            expiration_date=None,
            received_quantity=100,
            quantity=50,
            unit_cost=Decimal('10.00'),
        )
        expected = f'{product.name} — sem validade (50)'
        assert str(lot) == expected

    def test_stock_lot_str_zero_quantity(self):
        """__str__ com quantidade zero"""
        product = ProductFactory(name='Produto Teste')
        lot = StockLot.objects.create(
            product=product,
            expiration_date=timezone.localdate() + timedelta(days=30),
            received_quantity=100,
            quantity=0,
            unit_cost=Decimal('10.00'),
        )
        expected = f'{product.name} — {lot.expiration_date} (0)'
        assert str(lot) == expected


@pytest.mark.django_db
class TestFinancialEntryStr:
    """Teste para FinancialEntry.__str__ (linha 219-220)"""

    def test_financial_entry_str_format(self):
        """__str__ deve retornar 'Tipo: Descrição — R$ Valor'"""
        entry = FinancialEntry.objects.create(
            kind='expense',
            category='aluguel',
            description='Aluguel do escritório',
            amount=Decimal('1500.00'),
            entry_date=timezone.localdate(),
        )
        expected = 'Despesa operacional: Aluguel do escritório — R$ 1500.00'
        assert str(entry) == expected

    def test_financial_entry_str_investment(self):
        """__str__ para investimento"""
        entry = FinancialEntry.objects.create(
            kind='investment',
            category='equipamentos',
            description='Compra de computador',
            amount=Decimal('5000.00'),
            entry_date=timezone.localdate(),
        )
        expected = 'Investimento em ativo: Compra de computador — R$ 5000.00'
        assert str(entry) == expected

    def test_financial_entry_str_all_categories(self):
        """Testar todas as categorias"""
        for category in ['aluguel', 'pessoal', 'tributos', 'frete', 'contas', 'marketing', 'manutencao', 'equipamentos', 'outros']:
            entry = FinancialEntry.objects.create(
                kind='expense',
                category=category,
                description=f'Teste {category}',
                amount=Decimal('100.00'),
                entry_date=timezone.localdate(),
            )
            assert 'Despesa operacional' in str(entry)
            assert f'Teste {category}' in str(entry)
            assert 'R$ 100.00' in str(entry)


@pytest.mark.django_db
class TestProductProperties:
    """Testes para properties do Product"""

    def test_margin_property(self):
        """Property margin deve calcular sale_price - purchase_price"""
        product = ProductFactory(sale_price=Decimal('20.00'), purchase_price=Decimal('12.00'))
        assert product.margin == Decimal('8.00')

    def test_margin_property_zero_sale_price(self):
        """Margin com sale_price zero deve retornar 0"""
        product = ProductFactory(sale_price=Decimal('0.00'), purchase_price=Decimal('10.00'))
        assert product.margin == Decimal('0.00')

    def test_margin_property_no_sale_price(self):
        """Margin sem sale_price (None) deve retornar 0"""
        product = ProductFactory()
        # sale_price não pode ser None no banco, mas a property trata caso seja
        product.sale_price = None
        # Não salvar, apenas testar a property
        assert product.margin == Decimal('0.00')


@pytest.mark.django_db
class TestSaleProperties:
    """Testes para properties do Sale"""

    def test_subtotal_property(self):
        """subtotal deve somar unit_price * quantity de todos os itens"""
        sale = SaleFactory()
        product = ProductFactory(sale_price=Decimal('10.00'))
        SaleItemFactory(sale=sale, product=product, quantity=5, unit_price=Decimal('10.00'))
        SaleItemFactory(sale=sale, product=product, quantity=3, unit_price=Decimal('10.00'))
        assert sale.subtotal == Decimal('80.00')

    def test_total_property_without_discount(self):
        """total sem desconto deve igualar subtotal"""
        sale = SaleFactory(discount=Decimal('0.00'))
        product = ProductFactory(sale_price=Decimal('10.00'))
        SaleItemFactory(sale=sale, product=product, quantity=5, unit_price=Decimal('10.00'))
        assert sale.total == Decimal('50.00')

    def test_total_property_with_discount(self):
        """total com desconto deve ser subtotal - discount"""
        sale = SaleFactory(discount=Decimal('5.00'))
        product = ProductFactory(sale_price=Decimal('10.00'))
        SaleItemFactory(sale=sale, product=product, quantity=5, unit_price=Decimal('10.00'))
        assert sale.total == Decimal('45.00')

    def test_total_property_discount_exceeds_subtotal(self):
        """total não deve ser negativo (max com 0)"""
        sale = SaleFactory(discount=Decimal('100.00'))
        product = ProductFactory(sale_price=Decimal('10.00'))
        SaleItemFactory(sale=sale, product=product, quantity=5, unit_price=Decimal('10.00'))
        assert sale.total == Decimal('0.00')

    def test_refunded_amount_canceled(self):
        """refunded_amount deve retornar total se cancelado"""
        sale = SaleFactory()
        product = ProductFactory(sale_price=Decimal('10.00'))
        SaleItemFactory(sale=sale, product=product, quantity=5, unit_price=Decimal('10.00'))
        sale.canceled_at = timezone.now()
        sale.save()
        assert sale.refunded_amount == sale.total

    def test_refunded_amount_not_canceled(self):
        """refunded_amount deve retornar 0 se não cancelado"""
        sale = SaleFactory()
        assert sale.refunded_amount == Decimal('0')


@pytest.mark.django_db
class TestSaleItemProperties:
    """Testes para properties do SaleItem"""

    def test_subtotal_property(self):
        """subtotal deve ser unit_price * quantity"""
        item = SaleItemFactory(quantity=5, unit_price=Decimal('10.00'))
        assert item.subtotal == Decimal('50.00')

    def test_subtotal_zero_quantity(self):
        """subtotal com quantity zero"""
        item = SaleItemFactory(quantity=0, unit_price=Decimal('10.00'))
        assert item.subtotal == Decimal('0.00')


@pytest.mark.django_db
class TestModelTimestamps:
    """Testes para timestamps automáticos"""

    def test_product_created_at_auto(self):
        """Product.created_at deve ser preenchido automaticamente"""
        product = ProductFactory()
        assert product.created_at is not None

    def test_sale_created_at_auto(self):
        """Sale.created_at deve ser preenchido automaticamente"""
        sale = SaleFactory()
        assert sale.created_at is not None

    def test_stock_movement_created_at_auto(self):
        """StockMovement.created_at deve ser preenchido automaticamente"""
        product = ProductFactory()
        movement = StockMovement.objects.create(
            product=product,
            delta=10,
            stock_before=0,
            stock_after=10,
            reason='adjustment',
        )
        assert movement.created_at is not None

    def test_financial_entry_created_at_auto(self):
        """FinancialEntry.created_at deve ser preenchido automaticamente"""
        entry = FinancialEntry.objects.create(
            kind='expense',
            category='aluguel',
            description='Teste',
            amount=Decimal('100.00'),
            entry_date=timezone.localdate(),
        )
        assert entry.created_at is not None


@pytest.mark.django_db
class TestProductActiveByDefault:
    """Teste para Product.active default=True"""

    def test_product_active_by_default(self):
        """Produto deve ser active=True por padrão"""
        product = ProductFactory()
        assert product.active is True

    def test_product_can_be_inactive(self):
        """Produto pode ser criado como inactive"""
        product = ProductFactory(active=False)
        assert product.active is False


@pytest.mark.django_db
class TestStockLotAllocation:
    """Testes para StockLotAllocation"""

    def test_allocation_creation(self):
        """Criar alocação"""
        product = ProductFactory()
        lot = StockLot.objects.create(
            product=product,
            received_quantity=100,
            quantity=100,
            unit_cost=Decimal('10.00'),
        )
        movement = StockMovement.objects.create(
            product=product,
            delta=-10,
            stock_before=100,
            stock_after=90,
            reason='sale',
        )
        allocation = StockLotAllocation.objects.create(
            movement=movement,
            lot=lot,
            quantity=10,
        )
        assert allocation.movement == movement
        assert allocation.lot == lot
        assert allocation.quantity == 10