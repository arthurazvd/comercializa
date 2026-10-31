from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_stock_lots'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IdempotencyRecord',
            fields=[
                ('key', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('path', models.CharField(max_length=240)),
                ('request_hash', models.CharField(max_length=64)),
                ('response_status', models.PositiveSmallIntegerField()),
                ('response_body', models.JSONField(default=dict, encoder=DjangoJSONEncoder)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Operação idempotente',
                'verbose_name_plural': 'Operações idempotentes',
            },
        ),
    ]
