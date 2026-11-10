"""Testes abrangentes para financial_entries.py - cobre todas as ramificações (happy/sad paths)."""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import FinancialEntry, Category, Product
from tests.factories import CategoryFactory, ProductFactory
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestFinancialEntrySerializer:
    """Testes para FinancialEntrySerializer (linhas 17-36)"""

    def test_serializer_valid_data(self):
        """Serializer com dados válidos"""
        from core.financial_entries import FinancialEntrySerializer
        data = {
            'kind': 'expense',
            'category': 'aluguel',
            'description': 'Aluguel do mês',
            'amount': '1000.00',
            'entry_date': date.today().isoformat(),
        }
        serializer = FinancialEntrySerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_serializer_invalid_amount_zero(self):
        """Valor zero deve ser rejeitado (linha 28-29)"""
        from core.financial_entries import FinancialEntrySerializer
        data = {
            'kind': 'expense',
            'category': 'aluguel',
            'description': 'Aluguel do mês',
            'amount': '0.00',
            'entry_date': date.today().isoformat(),
        }
        serializer = FinancialEntrySerializer(data=data)
        assert not serializer.is_valid()
        assert 'amount' in serializer.errors
        assert 'maior que zero' in str(serializer.errors['amount'])

    def test_serializer_invalid_amount_negative(self):
        """Valor negativo deve ser rejeitado (linha 28-29)"""
        from core.financial_entries import FinancialEntrySerializer
        data = {
            'kind': 'expense',
            'category': 'aluguel',
            'description': 'Aluguel do mês',
            'amount': '-100.00',
            'entry_date': date.today().isoformat(),
        }
        serializer = FinancialEntrySerializer(data=data)
        assert not serializer.is_valid()
        assert 'amount' in serializer.errors
        assert 'maior que zero' in str(serializer.errors['amount'])

    def test_serializer_invalid_description_too_short(self):
        """Descrição com menos de 3 caracteres deve ser rejeitada (linha 32-35)"""
        from core.financial_entries import FinancialEntrySerializer
        data = {
            'kind': 'expense',
            'category': 'aluguel',
            'description': 'A',
            'amount': '100.00',
            'entry_date': date.today().isoformat(),
        }
        serializer = FinancialEntrySerializer(data=data)
        assert not serializer.is_valid()
        assert 'description' in serializer.errors
        assert 'pelo menos 3 caracteres' in str(serializer.errors['description'])

    def test_serializer_invalid_description_whitespace_only(self):
        """Descrição só com espaços deve ser rejeitada"""
        from core.financial_entries import FinancialEntrySerializer
        data = {
            'kind': 'expense',
            'category': 'aluguel',
            'description': '   ',
            'amount': '100.00',
            'entry_date': date.today().isoformat(),
        }
        serializer = FinancialEntrySerializer(data=data)
        assert not serializer.is_valid()
        assert 'description' in serializer.errors

    def test_serializer_valid_description_exact_three_chars(self):
        """Descrição com exatamente 3 caracteres deve ser aceita"""
        from core.financial_entries import FinancialEntrySerializer
        data = {
            'kind': 'expense',
            'category': 'aluguel',
            'description': 'ABC',
            'amount': '100.00',
            'entry_date': date.today().isoformat(),
        }
        serializer = FinancialEntrySerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_serializer_description_stripped(self):
        """Descrição deve ter espaços removidos"""
        from core.financial_entries import FinancialEntrySerializer
        data = {
            'kind': 'expense',
            'category': 'aluguel',
            'description': '  Aluguel do mês  ',
            'amount': '100.00',
            'entry_date': date.today().isoformat(),
        }
        serializer = FinancialEntrySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['description'] == 'Aluguel do mês'

    def test_serializer_invalid_kind(self):
        """Kind inválido deve ser rejeitado"""
        from core.financial_entries import FinancialEntrySerializer
        data = {
            'kind': 'invalid',
            'category': 'aluguel',
            'description': 'Aluguel do mês',
            'amount': '100.00',
            'entry_date': date.today().isoformat(),
        }
        serializer = FinancialEntrySerializer(data=data)
        assert not serializer.is_valid()
        assert 'kind' in serializer.errors

    def test_serializer_invalid_category(self):
        """Category inválida deve ser rejeitada"""
        from core.financial_entries import FinancialEntrySerializer
        data = {
            'kind': 'expense',
            'category': 'invalid_category',
            'description': 'Aluguel do mês',
            'amount': '100.00',
            'entry_date': date.today().isoformat(),
        }
        serializer = FinancialEntrySerializer(data=data)
        assert not serializer.is_valid()
        assert 'category' in serializer.errors

    def test_serializer_missing_required_fields(self):
        """Campos obrigatórios ausentes devem ser rejeitados"""
        from core.financial_entries import FinancialEntrySerializer
        data = {}
        serializer = FinancialEntrySerializer(data=data)
        assert not serializer.is_valid()
        assert 'kind' in serializer.errors
        assert 'category' in serializer.errors
        assert 'description' in serializer.errors
        assert 'amount' in serializer.errors
        assert 'entry_date' in serializer.errors

    def test_serializer_read_only_fields(self):
        """Campos read_only não devem ser definíveis"""
        from core.financial_entries import FinancialEntrySerializer
        entry = FinancialEntry.objects.create(
            kind='expense',
            category='aluguel',
            description='Aluguel do mês',
            amount=Decimal('1000.00'),
            entry_date=date.today(),
        )
        data = {
            'id': 999,
            'kind_display': 'Test',
            'category_display': 'Test',
            'created_at': '2020-01-01T00:00:00Z',
            'voided_at': '2020-01-01T00:00:00Z',
        }
        serializer = FinancialEntrySerializer(entry, data=data, partial=True)
        assert serializer.is_valid()
        # Campos read_only não devem ser alterados
        assert serializer.validated_data.get('id') is None
        assert serializer.validated_data.get('kind_display') is None


@pytest.mark.django_db
class TestFinancialEntriesView:
    """Testes para FinancialEntriesView (linhas 39-51)"""

    def test_list_entries(self):
        """Listar lançamentos"""
        client = APIClient()
        FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel',
            amount=Decimal('1000.00'), entry_date=date.today()
        )
        FinancialEntry.objects.create(
            kind='investment', category='equipamentos', description='Equipamento',
            amount=Decimal('5000.00'), entry_date=date.today()
        )
        response = client.get("/api/finance/entries/")
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_list_entries_filters_by_date(self):
        """Listar lançamentos filtrados por data (linha 46-47)"""
        client = APIClient()
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel ontem',
            amount=Decimal('1000.00'), entry_date=yesterday
        )
        FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel hoje',
            amount=Decimal('1000.00'), entry_date=today
        )
        FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel amanhã',
            amount=Decimal('1000.00'), entry_date=tomorrow
        )

        response = client.get(f"/api/finance/entries/?start={today.isoformat()}&end={today.isoformat()}")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['description'] == 'Aluguel hoje'

    def test_list_entries_excludes_voided(self):
        """Lançamentos anulados não devem aparecer na listagem"""
        client = APIClient()
        entry = FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel',
            amount=Decimal('1000.00'), entry_date=date.today()
        )
        entry.voided_at = timezone.now()
        entry.save()

        response = client.get("/api/finance/entries/")
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_create_entry(self):
        """Criar lançamento (linha 50-51)"""
        client = APIClient()
        user = User.objects.create_user(username='testuser', password='testpass123')
        client.force_authenticate(user=user)

        data = {
            'kind': 'expense',
            'category': 'aluguel',
            'description': 'Aluguel do mês',
            'amount': '1000.00',
            'entry_date': date.today().isoformat(),
        }
        response = client.post("/api/finance/entries/", data, format="json")
        assert response.status_code == 201
        assert response.data['description'] == 'Aluguel do mês'
        assert response.data['kind'] == 'expense'
        assert response.data['category'] == 'aluguel'
        assert FinancialEntry.objects.filter(description='Aluguel do mês').exists()

    def test_create_entry_sets_created_by(self):
        """created_by deve ser definido com o usuário autenticado"""
        client = APIClient()
        user = User.objects.create_user(username='testuser', password='testpass123')
        client.force_authenticate(user=user)

        data = {
            'kind': 'expense',
            'category': 'aluguel',
            'description': 'Aluguel do mês',
            'amount': '1000.00',
            'entry_date': date.today().isoformat(),
        }
        response = client.post("/api/finance/entries/", data, format="json")
        assert response.status_code == 201
        entry = FinancialEntry.objects.get(description='Aluguel do mês')
        assert entry.created_by == user

    def test_create_entry_unauthenticated(self):
        """Usuário não autenticado deve ter created_by = None"""
        client = APIClient()

        data = {
            'kind': 'expense',
            'category': 'aluguel',
            'description': 'Aluguel do mês',
            'amount': '1000.00',
            'entry_date': date.today().isoformat(),
        }
        response = client.post("/api/finance/entries/", data, format="json")
        assert response.status_code == 201
        entry = FinancialEntry.objects.get(description='Aluguel do mês')
        assert entry.created_by is None

    def test_create_invalid_data(self):
        """Criar com dados inválidos deve falhar"""
        client = APIClient()
        data = {
            'kind': 'expense',
            'category': 'aluguel',
            'description': 'A',  # Muito curto
            'amount': '1000.00',
            'entry_date': date.today().isoformat(),
        }
        response = client.post("/api/finance/entries/", data, format="json")
        assert response.status_code == 400
        assert 'description' in response.data


@pytest.mark.django_db
class TestFinancialEntryVoidView:
    """Testes para FinancialEntryVoidView (linhas 54-66) - cobre linhas 44-48, 57-58, 65-66"""

    def test_void_entry_success(self):
        """Anular lançamento com sucesso"""
        client = APIClient()
        entry = FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel',
            amount=Decimal('1000.00'), entry_date=date.today()
        )
        assert entry.voided_at is None

        response = client.post(f"/api/finance/entries/{entry.pk}/void/")
        assert response.status_code == 200
        assert response.data['voided_at'] is not None
        entry.refresh_from_db()
        assert entry.voided_at is not None
        assert entry.voided_by is None

    def test_void_entry_authenticated_sets_voided_by(self):
        """Anular com usuário autenticado define voided_by"""
        client = APIClient()
        user = User.objects.create_user(username='testuser', password='testpass123')
        client.force_authenticate(user=user)

        entry = FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel',
            amount=Decimal('1000.00'), entry_date=date.today()
        )

        response = client.post(f"/api/finance/entries/{entry.pk}/void/")
        assert response.status_code == 200
        entry.refresh_from_db()
        assert entry.voided_by == user

    def test_void_already_voided_returns_same_data_idempotent(self):
        """Anular já anulado deve retornar dados sem erro (linha 57-58)"""
        client = APIClient()
        entry = FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel',
            amount=Decimal('1000.00'), entry_date=date.today()
        )
        entry.voided_at = timezone.now()
        entry.save()

        response = client.post(f"/api/finance/entries/{entry.pk}/void/")
        assert response.status_code == 200
        assert 'X-Idempotent-Replay' in response.headers
        assert response.headers['X-Idempotent-Replay'] == 'true'
        assert response.data['voided_at'] is not None

    def test_void_nonexistent_entry(self):
        """Anular lançamento inexistente deve retornar 404"""
        client = APIClient()
        response = client.post("/api/finance/entries/99999/void/")
        assert response.status_code == 404

    def test_void_uses_select_for_update(self):
        """Deve usar select_for_update para evitar race conditions"""
        # Este teste verifica que a lógica de concorrência está presente
        # O teste real de concorrência seria complexo, mas verificamos o código
        from core.financial_entries import FinancialEntryVoidView
        import inspect
        source = inspect.getsource(FinancialEntryVoidView.post)
        assert 'select_for_update' in source

    def test_void_in_transaction(self):
        """Deve usar transaction.atomic"""
        from core.financial_entries import FinancialEntryVoidView
        import inspect
        source = inspect.getsource(FinancialEntryVoidView.post)
        assert 'transaction.atomic' in source

    def test_void_preserves_history(self):
        """Anulação deve preservar histórico (não deletar)"""
        client = APIClient()
        entry = FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel',
            amount=Decimal('1000.00'), entry_date=date.today()
        )
        entry_id = entry.pk

        response = client.post(f"/api/finance/entries/{entry_id}/void/")
        assert response.status_code == 200

        # Entrada ainda deve existir no banco
        entry.refresh_from_db()
        assert entry.pk == entry_id
        assert entry.description == 'Aluguel'
        assert entry.amount == Decimal('1000.00')
        assert entry.voided_at is not None


@pytest.mark.django_db
class TestFinancialEntryEdgeCases:
    """Testes de casos de borda"""

    def test_void_entry_idempotent_multiple_calls(self):
        """Múltiplas chamadas de anulação devem ser idempotentes"""
        client = APIClient()
        entry = FinancialEntry.objects.create(
            kind='expense', category='aluguel', description='Aluguel',
            amount=Decimal('1000.00'), entry_date=date.today()
        )

        response1 = client.post(f"/api/finance/entries/{entry.pk}/void/")
        assert response1.status_code == 200
        voided_at_1 = response1.data['voided_at']

        response2 = client.post(f"/api/finance/entries/{entry.pk}/void/")
        assert response2.status_code == 200
        voided_at_2 = response2.data['voided_at']

        # Deve retornar o mesmo voided_at
        assert voided_at_1 == voided_at_2

    def test_kind_choices(self):
        """Testar todas as opções de kind"""
        for kind in ['expense', 'investment']:
            entry = FinancialEntry.objects.create(
                kind=kind, category='aluguel', description='Teste',
                amount=Decimal('100.00'), entry_date=date.today()
            )
            assert entry.kind == kind

    def test_category_choices(self):
        """Testar todas as opções de category"""
        for category in ['aluguel', 'pessoal', 'tributos', 'frete', 'contas', 'marketing', 'manutencao', 'equipamentos', 'outros']:
            entry = FinancialEntry.objects.create(
                kind='expense', category=category, description='Teste',
                amount=Decimal('100.00'), entry_date=date.today()
            )
            assert entry.category == category