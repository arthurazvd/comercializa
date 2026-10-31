from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0004_idempotency_operations')]

    operations = [
        migrations.AlterField(
            model_name='sale', name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
