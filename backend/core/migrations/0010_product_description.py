from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0009_financial_entries')]
    operations = [
        migrations.AddField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
    ]
