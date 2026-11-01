from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('core', '0006_sale_reversal')]
    operations = [
        migrations.AddField(
            model_name='product', name='image_updated_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.CreateModel(
            name='ProductImage', fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.BinaryField()),
                ('filename', models.CharField(max_length=100)),
                ('size', models.PositiveIntegerField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='image_record', to='core.product')),
            ],
        ),
    ]
