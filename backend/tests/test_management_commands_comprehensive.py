"""Testes abrangentes para management commands - bootstrap_admin.py e seed_demo.py"""
import pytest
import os
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth import get_user_model
from core.models import Category, Product, StockMovement
from tests.factories import CategoryFactory, ProductFactory
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

User = get_user_model()


@pytest.mark.django_db
class TestBootstrapAdminCommand:
    """Testes para bootstrap_admin.py (linhas 10-28) - cobre linhas 22, 24, 26"""

    def test_creates_admin_when_none_exists(self):
        """Deve criar admin quando não existe nenhum superuser"""
        with patch.dict(os.environ, {
            'INITIAL_ADMIN_USERNAME': 'admin',
            'INITIAL_ADMIN_PASSWORD': 'senha123456789',
            'INITIAL_ADMIN_EMAIL': 'admin@test.com'
        }):
            out = StringIO()
            call_command('bootstrap_admin', stdout=out)
            assert 'Conta administradora inicial criada' in out.getvalue()
            assert User.objects.filter(username='admin', is_superuser=True).exists()

    def test_idempotent_when_admin_exists(self):
        """Deve ser idempotente quando admin já existe"""
        User.objects.create_superuser(username='existing', email='e@test.com', password='senha123456789')

        with patch.dict(os.environ, {
            'INITIAL_ADMIN_USERNAME': 'admin',
            'INITIAL_ADMIN_PASSWORD': 'senha123456789',
        }):
            out = StringIO()
            call_command('bootstrap_admin', stdout=out)
            assert 'Administrador já existe' in out.getvalue()
            assert User.objects.count() == 1

    def test_raises_error_when_username_missing(self):
        """Deve levantar erro quando username não configurado (linha 22)"""
        with patch.dict(os.environ, {
            'INITIAL_ADMIN_PASSWORD': 'senha123456789',
        }, clear=True):
            with pytest.raises(CommandError) as exc:
                call_command('bootstrap_admin')
            assert 'configure INITIAL_ADMIN_USERNAME' in str(exc.value)

    def test_raises_error_when_password_missing(self):
        """Deve levantar erro quando password não configurado (linha 22)"""
        with patch.dict(os.environ, {
            'INITIAL_ADMIN_USERNAME': 'admin',
        }, clear=True):
            with pytest.raises(CommandError) as exc:
                call_command('bootstrap_admin')
            assert 'INITIAL_ADMIN_PASSWORD' in str(exc.value)

    def test_raises_error_when_password_too_short(self):
        """Deve levantar erro quando password tem menos de 12 caracteres (linha 24)"""
        with patch.dict(os.environ, {
            'INITIAL_ADMIN_USERNAME': 'admin',
            'INITIAL_ADMIN_PASSWORD': 'curta',
        }, clear=True):
            with pytest.raises(CommandError) as exc:
                call_command('bootstrap_admin')
            assert 'pelo menos 12 caracteres' in str(exc.value)

    def test_raises_error_when_username_exists_not_superuser(self):
        """Deve levantar erro quando username existe mas não é superuser (linha 26)"""
        User.objects.create_user(username='admin', password='senha123456789')

        with patch.dict(os.environ, {
            'INITIAL_ADMIN_USERNAME': 'admin',
            'INITIAL_ADMIN_PASSWORD': 'senha123456789',
        }, clear=True):
            with pytest.raises(CommandError) as exc:
                call_command('bootstrap_admin')
            assert 'já existe sem ser administrador' in str(exc.value)

    def test_creates_admin_with_email(self):
        """Deve criar admin com email"""
        with patch.dict(os.environ, {
            'INITIAL_ADMIN_USERNAME': 'admin',
            'INITIAL_ADMIN_PASSWORD': 'senha123456789',
            'INITIAL_ADMIN_EMAIL': 'admin@example.com',
        }, clear=True):
            call_command('bootstrap_admin')
            user = User.objects.get(username='admin')
            assert user.email == 'admin@example.com'

    def test_does_not_change_password_on_subsequent_runs(self):
        """Não deve alterar senha em execuções subsequentes"""
        with patch.dict(os.environ, {
            'INITIAL_ADMIN_USERNAME': 'admin',
            'INITIAL_ADMIN_PASSWORD': 'senha123456789',
        }, clear=True):
            call_command('bootstrap_admin')
            user = User.objects.get(username='admin')
            original_password = user.password

            # Executar novamente
            call_command('bootstrap_admin')
            user.refresh_from_db()
            assert user.password == original_password


@pytest.mark.django_db
class TestSeedDemoCommand:
    """Testes para seed_demo.py (linhas 48-89) - cobre linha 68"""

    def test_adds_catalog_products(self):
        """Deve adicionar produtos do catálogo"""
        out = StringIO()
        call_command('seed_demo', stdout=out)
        assert 'produto(s) inseridos/atualizados' in out.getvalue()
        assert Product.objects.count() > 0

    def test_idempotent_without_reset(self):
        """Deve ser idempotente sem --reset-demo"""
        call_command('seed_demo')
        count1 = Product.objects.count()
        call_command('seed_demo')
        count2 = Product.objects.count()
        assert count1 == count2

    def test_reset_demo_updates_existing_products(self):
        """--reset-demo deve atualizar produtos existentes"""
        # Criar produto com SKU do catálogo mas valores diferentes
        category = CategoryFactory(name='Utilidades domésticas')
        product = ProductFactory(
            sku='UTIL-001',
            category=category,
            name='Nome Antigo',
            stock=999,
            sale_price=Decimal('99.99'),
            purchase_price=Decimal('50.00'),
        )
        original_stock = product.stock

        call_command('seed_demo', '--reset-demo')
        product.refresh_from_db()
        # Deve ter atualizado para valores do catálogo
        assert product.name == 'Pote plástico hermético 1 L'
        assert product.stock == 34  # Valor do catálogo
        assert product.sale_price == Decimal('9.99')
        assert product.purchase_price == Decimal('5.40')

    def test_reset_demo_creates_stock_movement_for_stock_change(self):
        """--reset-demo deve criar StockMovement quando estoque muda"""
        category = CategoryFactory(name='Utilidades domésticas')
        product = ProductFactory(
            sku='UTIL-001',
            category=category,
            stock=100,  # Diferente do catálogo (34)
        )

        call_command('seed_demo', '--reset-demo')

        movements = StockMovement.objects.filter(product=product, reason='adjustment')
        assert movements.exists()
        movement = movements.first()
        assert 'Reinicialização explícita do catálogo demo' in movement.note
        assert movement.delta == 34 - 100  # Novo - antigo

    def test_reset_demo_product_not_found(self):
        """--reset-demo com produto não encontrado deve criar novo (linha 68)"""
        # Não criar produto com SKU UTIL-001
        # O comando deve criar novo
        call_command('seed_demo', '--reset-demo')
        assert Product.objects.filter(sku='UTIL-001').exists()
        product = Product.objects.get(sku='UTIL-001')
        assert product.name == 'Pote plástico hermético 1 L'

    def test_retire_legacy_deactivates_old_skus(self):
        """--retire-legacy deve desativar SKUs antigos"""
        legacy_skus = ['ARROZ-01', 'FEIJAO-01', 'LEITE-01', 'REFRI-01', 'BISC-01', 'DET-01']
        for sku in legacy_skus:
            ProductFactory(sku=sku, active=True)

        out = StringIO()
        call_command('seed_demo', '--retire-legacy', stdout=out)
        assert 'produtos antigos de supermercado desativados' in out.getvalue()

        for sku in legacy_skus:
            product = Product.objects.get(sku=sku)
            assert product.active is False

    def test_retire_legacy_only_affects_active(self):
        """--retire-legacy deve afetar apenas ativos"""
        ProductFactory(sku='ARROZ-01', active=False)
        ProductFactory(sku='FEIJAO-01', active=True)

        call_command('seed_demo', '--retire-legacy')

        arroz = Product.objects.get(sku='ARROZ-01')
        feijao = Product.objects.get(sku='FEIJAO-01')
        assert arroz.active is False  # Já era inativo
        assert feijao.active is False  # Deve ter desativado

    def test_catalog_products_have_correct_data(self):
        """Produtos do catálogo devem ter dados corretos"""
        call_command('seed_demo')

        pote = Product.objects.get(sku='UTIL-001')
        assert pote.name == 'Pote plástico hermético 1 L'
        assert pote.category.name == 'Utilidades domésticas'
        assert pote.purchase_price == Decimal('5.40')
        assert pote.sale_price == Decimal('9.99')
        assert pote.stock == 34
        assert pote.minimum_stock == 8
        assert pote.perishable is False
        assert pote.active is True

    def test_perishable_products_have_expiration(self):
        """Produtos perecíveis devem ter data de validade"""
        call_command('seed_demo')

        creme = Product.objects.get(sku='BELE-003')
        assert creme.perishable is True
        assert creme.expiration_date is not None
        assert creme.expiration_date > timezone.localdate()

    def test_expired_perishable_product(self):
        """Produto perecível vencido (expiry negativo)"""
        call_command('seed_demo')

        sabonete = Product.objects.get(sku='BELE-004')
        assert sabonete.perishable is True
        assert sabonete.expiration_date is not None
        assert sabonete.expiration_date < timezone.localdate()

    def test_zero_stock_products(self):
        """Produtos com estoque zero"""
        call_command('seed_demo')

        adaptador = Product.objects.get(sku='ELEC-005')
        assert adaptador.stock == 0
        assert adaptador.active is True

    def test_all_catalog_categories_created(self):
        """Todas as categorias do catálogo devem ser criadas"""
        call_command('seed_demo')

        expected_categories = [
            'Utilidades domésticas', 'Vestuário e acessórios', 'Eletrônicos e acessórios',
            'Papelaria e presentes', 'Brinquedos e lazer', 'Festas e decoração',
            'Beleza e cuidados', 'Pet shop', 'Ferramentas e acessórios'
        ]
        for cat_name in expected_categories:
            assert Category.objects.filter(name=cat_name).exists()