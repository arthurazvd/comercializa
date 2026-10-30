"""Catálogo de demonstração de loja de variedades, sem sobrescrever o estoque real."""
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from core.models import Category, Product, StockMovement


CATALOG = [
    # Categoria, nome, sku, compra, venda, quantidade, mínimo, validade em dias
    ('Utilidades domésticas', 'Pote plástico hermético 1 L', 'UTIL-001', '5.40', '9.99', 34, 8, None),
    ('Utilidades domésticas', 'Conjunto 3 vasilhas plásticas', 'UTIL-002', '11.90', '19.99', 12, 6, None),
    ('Utilidades domésticas', 'Bacia plástica 8 L', 'UTIL-003', '6.00', '12.99', 5, 8, None),
    ('Utilidades domésticas', 'Organizador de gaveta', 'UTIL-004', '4.20', '8.99', 18, 6, None),
    ('Utilidades domésticas', 'Balde plástico 10 L', 'UTIL-005', '9.80', '17.90', 14, 5, None),
    ('Utilidades domésticas', 'Pregador de roupas 12 un.', 'UTIL-006', '2.10', '4.99', 46, 10, None),
    ('Vestuário e acessórios', 'Boné aba curva liso', 'VEST-001', '12.00', '24.90', 27, 6, None),
    ('Vestuário e acessórios', 'Chapéu de palha tradicional', 'VEST-002', '10.00', '22.90', 7, 8, None),
    ('Vestuário e acessórios', 'Óculos de sol casual', 'VEST-003', '7.60', '16.99', 19, 5, None),
    ('Vestuário e acessórios', 'Chinelo básico unissex', 'VEST-004', '8.50', '17.99', 18, 7, None),
    ('Eletrônicos e acessórios', 'Carregador USB-C 20 W', 'ELEC-001', '15.00', '29.99', 28, 8, None),
    ('Eletrônicos e acessórios', 'Cabo USB-C 1 m', 'ELEC-002', '4.80', '12.99', 40, 12, None),
    ('Eletrônicos e acessórios', 'Fone de ouvido com fio P2', 'ELEC-003', '8.90', '19.99', 4, 6, None),
    ('Eletrônicos e acessórios', 'Suporte de celular para mesa', 'ELEC-004', '6.40', '14.99', 20, 5, None),
    ('Eletrônicos e acessórios', 'Adaptador USB-A para USB-C', 'ELEC-005', '3.30', '7.99', 0, 10, None),
    ('Papelaria e presentes', 'Caderno pequeno 96 folhas', 'PAP-001', '6.00', '12.99', 34, 10, None),
    ('Papelaria e presentes', 'Caneta esferográfica azul', 'PAP-002', '0.90', '1.99', 75, 20, None),
    ('Papelaria e presentes', 'Estojo escolar simples', 'PAP-003', '4.20', '9.99', 23, 8, None),
    ('Papelaria e presentes', 'Papel de presente estampado', 'PAP-004', '1.40', '3.99', 29, 8, None),
    ('Brinquedos e lazer', 'Bola de plástico colorida', 'BRIN-001', '3.50', '9.99', 40, 10, None),
    ('Brinquedos e lazer', 'Carrinho miniatura', 'BRIN-002', '4.60', '11.99', 11, 10, None),
    ('Brinquedos e lazer', 'Pula corda infantil', 'BRIN-003', '5.00', '12.99', 0, 6, None),
    ('Festas e decoração', 'Balões coloridos 50 un.', 'FEST-001', '6.20', '12.99', 16, 6, None),
    ('Festas e decoração', 'Vela aniversário sortida', 'FEST-002', '1.20', '3.99', 37, 12, None),
    ('Festas e decoração', 'Fita decorativa metalizada', 'FEST-003', '2.20', '5.99', 9, 8, None),
    ('Beleza e cuidados', 'Elástico de cabelo 20 un.', 'BELE-001', '1.50', '4.99', 30, 8, None),
    ('Beleza e cuidados', 'Escova de cabelo compacta', 'BELE-002', '3.40', '8.99', 17, 6, None),
    ('Beleza e cuidados', 'Creme hidratante 120 ml', 'BELE-003', '6.30', '12.99', 6, 8, 12),
    ('Beleza e cuidados', 'Sabonete líquido 250 ml', 'BELE-004', '4.50', '9.99', 9, 5, -3),
    ('Pet shop', 'Tigela plástica para pet', 'PET-001', '3.70', '9.99', 18, 5, None),
    ('Pet shop', 'Brinquedo bolinha para pet', 'PET-002', '2.50', '6.99', 13, 5, None),
    ('Ferramentas e acessórios', 'Fita isolante 10 m', 'FERR-001', '2.20', '5.99', 22, 8, None),
    ('Ferramentas e acessórios', 'Lanterna LED pequena', 'FERR-002', '8.70', '18.99', 15, 6, None),
]


class Command(BaseCommand):
    help = 'Adiciona catálogo de variedades, sem modificar produtos existentes. --reset-demo atualiza apenas SKUs da demonstração.'

    def add_arguments(self, parser):
        parser.add_argument('--reset-demo', action='store_true', help='Reinicia SKUs demo, inclusive saldos (com auditoria). Usar só em ambiente de testes.')
        parser.add_argument('--retire-legacy', action='store_true', help='Desativa os seis SKUs antigos de supermercado, se estiverem presentes.')

    def handle(self, *args, **options):
        count = 0
        today = timezone.localdate()
        for category_name, name, sku, cost, price, stock, minimum, expiry in CATALOG:
            category, _ = Category.objects.get_or_create(name=category_name)
            defaults = dict(name=name, category=category, purchase_price=Decimal(cost),
                            sale_price=Decimal(price), stock=stock, minimum_stock=minimum,
                            expiration_date=today + timedelta(days=expiry) if expiry is not None else None,
                            active=True, perishable=expiry is not None)
            if options['reset_demo']:
                with transaction.atomic():
                    product = Product.objects.select_for_update().filter(sku=sku).first()
                    if product is None:
                        Product.objects.create(sku=sku, **defaults)
                    else:
                        before = product.stock
                        for key, value in defaults.items():
                            setattr(product, key, value)
                        product.save()
                        if before != stock:
                            StockMovement.objects.create(
                                product=product, delta=stock - before,
                                stock_before=before, stock_after=stock,
                                reason=StockMovement.Reason.ADJUSTMENT,
                                note='Reinicialização explícita do catálogo demo',
                            )
                count += 1
            else:
                _, created = Product.objects.get_or_create(sku=sku, defaults=defaults)
                count += int(created)
        if options['retire_legacy']:
            legacy_skus = ['ARROZ-01', 'FEIJAO-01', 'LEITE-01', 'REFRI-01', 'BISC-01', 'DET-01']
            retired = Product.objects.filter(sku__in=legacy_skus, active=True).update(active=False)
            self.stdout.write(self.style.WARNING(f'{retired} produtos antigos de supermercado desativados; histórico preservado.'))
        self.stdout.write(self.style.SUCCESS(f'Catálogo de demonstração: {count} produto(s) inseridos/atualizados.'))
