from django.db import migrations, models
import django.db.models.deletion


def populate_existing_lot_costs(apps, schema_editor):
    # O custo histórico dos lotes antigos não existe nos dados anteriores.
    # Inicializa pelo custo de referência conhecido na migração; não fabrica compras.
    Lot = apps.get_model('core', 'StockLot')
    for lot in Lot.objects.select_related('product').iterator(chunk_size=500):
        Lot.objects.filter(pk=lot.pk).update(unit_cost=lot.product.purchase_price)


class Migration(migrations.Migration):
    dependencies = [('core', '0007_product_image')]
    operations = [
        migrations.AlterField(model_name='stocklot', name='expiration_date', field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='stocklot', name='unit_cost', field=models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        migrations.AddField(model_name='stockmovement', name='unit_cost', field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
        migrations.AddField(model_name='saleitem', name='cost_total', field=models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
        migrations.RunPython(populate_existing_lot_costs, migrations.RunPython.noop),
    ]
