from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Category, Product

class Command(BaseCommand):
    help = "Cria dados básicos para testar o Comercializa."

    def handle(self, *args, **options):
        alimentos, _ = Category.objects.get_or_create(name="Alimentos")
        bebidas, _ = Category.objects.get_or_create(name="Bebidas")
        limpeza, _ = Category.objects.get_or_create(name="Limpeza")

        today = timezone.localdate()
        data = [
            ("Arroz 1kg", alimentos, "ARROZ-01", 5.50, 7.99, 4, 5, None),
            ("Feijão 1kg", alimentos, "FEIJAO-01", 6.00, 8.49, 18, 5, None),
            ("Leite 1L", bebidas, "LEITE-01", 4.10, 5.49, 12, 6, today + timedelta(days=8)),
            ("Refrigerante 2L", bebidas, "REFRI-01", 6.20, 9.50, 20, 8, None),
            ("Biscoito", alimentos, "BISC-01", 2.00, 3.50, 15, 5, today + timedelta(days=12)),
            ("Detergente", limpeza, "DET-01", 1.50, 2.75, 3, 4, None),
        ]

        for name, category, sku, buy, sale, stock, minimum, expiration in data:
            Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": category,
                    "purchase_price": buy,
                    "sale_price": sale,
                    "stock": stock,
                    "minimum_stock": minimum,
                    "expiration_date": expiration,
                    "active": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("Dados de demonstração criados."))
