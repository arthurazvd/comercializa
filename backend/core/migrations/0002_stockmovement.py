from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="StockMovement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("delta", models.IntegerField()),
                ("stock_before", models.PositiveIntegerField()),
                ("stock_after", models.PositiveIntegerField()),
                ("reason", models.CharField(choices=[("sale", "Venda"), ("adjustment", "Ajuste manual")], max_length=20)),
                ("note", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="stock_movements", to="core.product")),
                ("sale", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="stock_movements", to="core.sale")),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
    ]
