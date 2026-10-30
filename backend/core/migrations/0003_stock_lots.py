from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('core', '0002_stockmovement')]

    operations = [
        migrations.AddField(model_name='stockmovement', name='justification', field=models.CharField(max_length=30, choices=[('recebimento', 'Recebimento'), ('devolucao', 'Devolução'), ('avaria', 'Avaria / quebra'), ('perda', 'Descarte / vencimento'), ('inventario', 'Acerto de inventário'), ('outro', 'Outro')], default='', blank=True)),
        migrations.AddField(model_name="product", name="perishable", field=models.BooleanField(default=False)),
        migrations.CreateModel(
            name='StockLot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expiration_date', models.DateField()),
                ('received_quantity', models.PositiveIntegerField()),
                ('quantity', models.PositiveIntegerField()),
                ('receipt_movement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='received_lots', to='core.stockmovement')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lots', to='core.product')),
            ],
            options={'ordering': ['expiration_date', 'id']},
        ),
        migrations.CreateModel(
            name='StockLotAllocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('lot', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='allocations', to='core.stocklot')),
                ('movement', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lot_allocations', to='core.stockmovement')),
            ],
        ),
    ]
