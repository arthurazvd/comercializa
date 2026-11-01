from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0008_cost_by_lot'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FinancialEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('expense', 'Despesa operacional'), ('investment', 'Investimento em ativo')], max_length=16)),
                ('category', models.CharField(choices=[('aluguel', 'Aluguel'), ('pessoal', 'Pessoal'), ('tributos', 'Tributos e taxas'), ('frete', 'Frete'), ('contas', 'Água, energia e internet'), ('marketing', 'Marketing'), ('manutencao', 'Manutenção'), ('equipamentos', 'Equipamentos'), ('outros', 'Outros')], max_length=30)),
                ('description', models.CharField(max_length=200)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('entry_date', models.DateField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('voided_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='financial_entries', to=settings.AUTH_USER_MODEL)),
                ('voided_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='voided_financial_entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-entry_date', '-id']},
        ),
        migrations.AddIndex(model_name='financialentry', index=models.Index(fields=['kind', 'entry_date'], name='fin_kind_date_idx')),
    ]
