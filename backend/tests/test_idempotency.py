"""A mesma operação de escrita não pode ser aplicada duas vezes após timeout."""
import pytest
from rest_framework.test import APIClient

from core.models import Category, Product, Sale, StockMovement, IdempotencyRecord


@pytest.mark.django_db
def test_cadastro_repetido_com_chave_devolve_mesmo_produto():
    client = APIClient()
    key = 'cadastro-operacao-1234567890'
    data = {'name': 'Caneca', 'sale_price': '18.50', 'stock': 8}
    original = client.post('/api/products/', data, format='json', HTTP_IDEMPOTENCY_KEY=key)
    replay = client.post('/api/products/', data, format='json', HTTP_IDEMPOTENCY_KEY=key)
    assert original.status_code == replay.status_code == 201
    assert original.data['id'] == replay.data['id']
    assert replay['X-Idempotent-Replay'] == 'true'
    assert Product.objects.count() == 1
    assert IdempotencyRecord.objects.count() == 1


@pytest.mark.django_db
def test_mesma_chave_nao_pode_significar_cadastro_diferente():
    client = APIClient()
    key = 'operacao-conflito-1234567890'
    first = client.post('/api/categories/', {'name': 'Categoria A'}, format='json', HTTP_IDEMPOTENCY_KEY=key)
    changed = client.post('/api/categories/', {'name': 'Categoria B'}, format='json', HTTP_IDEMPOTENCY_KEY=key)
    assert first.status_code == 201
    assert changed.status_code == 409
    assert Category.objects.count() == 1


@pytest.mark.django_db
def test_repetir_venda_nao_baixa_estoque_duas_vezes():
    product = Product.objects.create(name='Copo', sale_price=10, stock=20)
    client = APIClient()
    payload = {'items': [{'product': product.pk, 'quantity': 3}], 'discount': '0.00'}
    key = 'venda-operacao-1234567890'
    first = client.post('/api/sales/', payload, format='json', HTTP_IDEMPOTENCY_KEY=key)
    second = client.post('/api/sales/', payload, format='json', HTTP_IDEMPOTENCY_KEY=key)
    product.refresh_from_db()
    assert first.status_code == second.status_code == 201
    assert first.data['id'] == second.data['id']
    assert product.stock == 17
    assert Sale.objects.count() == 1
    assert StockMovement.objects.count() == 1


@pytest.mark.django_db
def test_repetir_movimentacao_nao_muda_estoque_novamente():
    product = Product.objects.create(name='Balde', sale_price=10, stock=10)
    client = APIClient()
    payload = {'product': product.pk, 'delta': 5, 'note': 'Recebimento', 'justification': 'recebimento'}
    key = 'movimentacao-1234567890'
    first = client.post('/api/stock-movements/', payload, format='json', HTTP_IDEMPOTENCY_KEY=key)
    second = client.post('/api/stock-movements/', payload, format='json', HTTP_IDEMPOTENCY_KEY=key)
    product.refresh_from_db()
    assert first.status_code == second.status_code == 201
    assert first.data['id'] == second.data['id']
    assert product.stock == 15
    assert StockMovement.objects.count() == 1


@pytest.mark.django_db
def test_operacao_invalida_nao_cria_marcador_e_cliente_antigo_funciona():
    client = APIClient()
    invalid = client.post('/api/products/', {'name': '', 'sale_price': -1},
                          format='json', HTTP_IDEMPOTENCY_KEY='idempotencia-1234567890')
    assert invalid.status_code == 400
    assert IdempotencyRecord.objects.count() == 0
    old = client.post('/api/categories/', {'name': 'Sem cabeçalho'}, format='json')
    assert old.status_code == 201
    assert IdempotencyRecord.objects.count() == 0
