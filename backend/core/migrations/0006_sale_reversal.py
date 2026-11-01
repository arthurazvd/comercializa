from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_sale_timestamp_index'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(model_name='sale', name='canceled_at',
                            field=models.DateTimeField(null=True, blank=True, db_index=True)),
        migrations.AddField(model_name='sale', name='cancellation_reason',
                            field=models.CharField(max_length=255, blank=True, default='')),
        migrations.AddField(model_name='sale', name='canceled_by',
                            field=models.ForeignKey(to=settings.AUTH_USER_MODEL,
                                null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL,
                                related_name='canceled_sales')),
        migrations.AlterField(model_name='stockmovement', name='reason',
                              field=models.CharField(max_length=20, choices=[
                                  ('sale', 'Venda'), ('reversal', 'Estorno de venda'),
                                  ('adjustment', 'Ajuste manual')])),
    ]
