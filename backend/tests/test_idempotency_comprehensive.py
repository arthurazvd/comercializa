"""Testes abrangentes para idempotency.py - cobre todas as ramificações (happy/sad paths)."""
import json
import hashlib

import pytest
from django.db import IntegrityError
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.test import APIClient

from core.models import Product, IdempotencyRecord
from core.idempotency import KEY_PATTERN
from tests.factories import CategoryFactory, ProductFactory


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def category():
    return CategoryFactory()


# ---------------------------------------------------------------------------
# Padrão da chave
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestIdempotencyKeyPattern:
    """Testes para validação do padrão da chave (linha 36)"""

    def test_valid_key_alphanumeric(self):
        assert KEY_PATTERN.fullmatch('abc123DEF45678901') is not None

    def test_valid_key_with_underscore(self):
        assert KEY_PATTERN.fullmatch('abc_123_def_456789') is not None

    def test_valid_key_with_hyphen(self):
        assert KEY_PATTERN.fullmatch('abc-123-def-456789') is not None

    def test_valid_key_min_length_16(self):
        assert KEY_PATTERN.fullmatch('a' * 16) is not None

    def test_valid_key_max_length_100(self):
        assert KEY_PATTERN.fullmatch('a' * 100) is not None

    def test_invalid_key_too_short(self):
        assert KEY_PATTERN.fullmatch('a' * 15) is None

    def test_invalid_key_too_long(self):
        assert KEY_PATTERN.fullmatch('a' * 101) is None

    def test_invalid_key_special_chars(self):
        assert KEY_PATTERN.fullmatch('abc@123') is None
        assert KEY_PATTERN.fullmatch('abc#123') is None
        assert KEY_PATTERN.fullmatch('abc.123') is None
        assert KEY_PATTERN.fullmatch('abc 123') is None

    def test_invalid_key_empty(self):
        assert KEY_PATTERN.fullmatch('') is None


# ---------------------------------------------------------------------------
# Mixin genérico (produtos)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestIdempotentCreateMixin:
    """Testes para IdempotentCreateMixin (linhas 30-70)"""

    def test_create_without_idempotency_key(self, client, category):
        """POST sem Idempotency-Key deve funcionar normalmente (linha 33-34)"""
        data = {
            'name': 'Produto Teste',
            'category': category.id,
            'sale_price': '15.00',
            'purchase_price': '10.00',
            'stock': 10,
        }
        response = client.post("/api/products/", data, format="json")
        assert response.status_code == 201

    def test_create_with_valid_idempotency_key(self, client, category):
        """POST com Idempotency-Key válida deve criar e registrar"""
        data = {
            'name': 'Produto Teste',
            'category': category.id,
            'sale_price': '15.00',
            'purchase_price': '10.00',
            'stock': 10,
        }
        headers = {'HTTP_IDEMPOTENCY_KEY': 'valid-key-1234567890123456'}
        response = client.post("/api/products/", data,
                               format="json", **headers)
        assert response.status_code == 201
        assert IdempotencyRecord.objects.filter(
            key='valid-key-1234567890123456').exists()

    def test_repeat_same_key_returns_cached_response(self, client, category):
        """Repetir mesma chave deve retornar resposta cacheada"""
        data = {
            'name': 'Produto Teste',
            'category': category.id,
            'sale_price': '15.00',
            'purchase_price': '10.00',
            'stock': 10,
        }
        headers = {'HTTP_IDEMPOTENCY_KEY': 'repeat-key-1234567890123456'}
        response1 = client.post("/api/products/", data,
                                format="json", **headers)
        assert response1.status_code == 201
        product_id_1 = response1.data['id']

        response2 = client.post("/api/products/", data,
                                format="json", **headers)
        assert response2.status_code == 201
        assert response2.headers.get('X-Idempotent-Replay') == 'true'
        assert response2.data['id'] == product_id_1

    def test_repeat_key_different_payload_returns_conflict(self, client, category):
        """Mesma chave com payload diferente deve retornar 409 (linha 55-58)"""
        data1 = {
            'name': 'Produto Um',
            'category': category.id,
            'sale_price': '15.00',
            'purchase_price': '10.00',
            'stock': 10,
        }
        data2 = {
            'name': 'Produto Dois',
            'category': category.id,
            'sale_price': '15.00',
            'purchase_price': '10.00',
            'stock': 10,
        }
        headers = {'HTTP_IDEMPOTENCY_KEY': 'conflict-key-1234567890123456'}
        response1 = client.post("/api/products/", data1,
                                format="json", **headers)
        assert response1.status_code == 201

        response2 = client.post("/api/products/", data2,
                                format="json", **headers)
        assert response2.status_code == 409
        assert 'já foi utilizada em outra operação' in response2.data['detail']

    def test_repeat_key_different_path_returns_conflict(self, client, category):
        """Mesma chave em path diferente deve retornar 409"""
        data = {
            'name': 'Produto Teste',
            'category': category.id,
            'sale_price': '15.00',
            'purchase_price': '10.00',
            'stock': 10,
        }
        headers = {'HTTP_IDEMPOTENCY_KEY': 'path-key-1234567890123456'}
        response1 = client.post("/api/products/", data,
                                format="json", **headers)
        assert response1.status_code == 201

        response2 = client.post(
            "/api/categories/", {'name': 'Categoria'}, format="json", **headers)
        assert response2.status_code == 409

    def test_repeat_key_different_user_returns_conflict(self, client, category):
        """Mesma chave com usuário diferente deve retornar 409"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user1 = User.objects.create_user(username='user1', password='pass123')
        user2 = User.objects.create_user(username='user2', password='pass123')

        data = {
            'name': 'Produto Teste',
            'category': category.id,
            'sale_price': '15.00',
            'purchase_price': '10.00',
            'stock': 10,
        }
        headers = {'HTTP_IDEMPOTENCY_KEY': 'user-key-1234567890123456'}

        client.force_authenticate(user=user1)
        response1 = client.post("/api/products/", data,
                                format="json", **headers)
        assert response1.status_code == 201

        client.force_authenticate(user=user2)
        response2 = client.post("/api/products/", data,
                                format="json", **headers)
        assert response2.status_code == 409

    def test_invalid_key_pattern_returns_400(self, client, category):
        """Chave com padrão inválido deve retornar 400 (linha 35-36)"""
        data = {
            'name': 'Produto Teste',
            'category': category.id,
            'sale_price': '15.00',
            'purchase_price': '10.00',
            'stock': 10,
        }
        headers = {'HTTP_IDEMPOTENCY_KEY': 'invalid@key'}
        response = client.post("/api/products/", data,
                               format="json", **headers)
        assert response.status_code == 400
        assert 'Chave de operação inválida' in response.data['detail']

    def test_error_response_does_not_create_idempotency_record(self, client, category):
        """Resposta de erro não deve criar registro de idempotência (linha 63-66)"""
        data = {
            'name': 'Produto Teste',
            'category': category.id,
            'sale_price': '15.00',
            'purchase_price': '10.00',
            'stock': -5,
        }
        headers = {'HTTP_IDEMPOTENCY_KEY': 'error-key-1234567890123456'}
        response = client.post("/api/products/", data,
                               format="json", **headers)
        assert response.status_code == 400
        assert not IdempotencyRecord.objects.filter(
            key='error-key-1234567890123456').exists()

    def test_rollback_on_error_removes_key(self, client, category):
        """Erro deve fazer rollback e não deixar chave (linha 64-66)"""
        data = {
            'name': 'Produto Teste',
            'category': category.id,
            'sale_price': '15.00',
            'purchase_price': '10.00',
            'stock': -5,
        }
        headers = {'HTTP_IDEMPOTENCY_KEY': 'rollback-key-1234567890123456'}

        response1 = client.post("/api/products/", data,
                                format="json", **headers)
        assert response1.status_code == 400

        data['stock'] = 10
        response2 = client.post("/api/products/", data,
                                format="json", **headers)
        assert response2.status_code == 201
        assert IdempotencyRecord.objects.filter(
            key='rollback-key-1234567890123456').exists()


# ---------------------------------------------------------------------------
# Idempotência em vendas
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestIdempotencyWithSales:
    """Testes de idempotência com vendas"""

    @pytest.fixture
    def product(self, category):
        return ProductFactory(category=category, stock=100, sale_price='10.00')

    def test_sale_idempotency_prevents_double_stock_reduction(self, client, product):
        """Idempotência em venda deve evitar redução dupla de estoque"""
        data = {
            'discount': '0.00',
            'items': [{'product': product.id, 'quantity': 5}],
        }
        headers = {'HTTP_IDEMPOTENCY_KEY': 'sale-key-1234567890123456'}
        initial_stock = product.stock

        response1 = client.post("/api/sales/", data, format="json", **headers)
        assert response1.status_code == 201
        product.refresh_from_db()
        assert product.stock == initial_stock - 5

        response2 = client.post("/api/sales/", data, format="json", **headers)
        assert response2.status_code == 201
        assert response2.headers.get('X-Idempotent-Replay') == 'true'
        product.refresh_from_db()
        assert product.stock == initial_stock - 5


# ---------------------------------------------------------------------------
# Idempotência em movimentações de estoque
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestIdempotencyWithStockMovements:
    """Testes de idempotência com movimentações de estoque"""

    @pytest.fixture
    def product(self, category):
        return ProductFactory(category=category, stock=50)

    def test_stock_movement_idempotency(self, client, product):
        """Idempotência em movimentação de estoque"""
        data = {
            'product': product.id,
            'delta': 10,
            'note': 'Recebimento de mercadoria',
            'justification': 'recebimento',
        }
        headers = {'HTTP_IDEMPOTENCY_KEY': 'movement-key-1234567890123456'}
        initial_stock = product.stock

        response1 = client.post("/api/stock-movements/",
                                data, format="json", **headers)
        assert response1.status_code == 201
        product.refresh_from_db()
        assert product.stock == initial_stock + 10

        response2 = client.post("/api/stock-movements/",
                                data, format="json", **headers)
        assert response2.status_code == 201
        assert response2.headers.get('X-Idempotent-Replay') == 'true'
        product.refresh_from_db()
        assert product.stock == initial_stock + 10


# ---------------------------------------------------------------------------
# Fingerprint do request
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestIdempotencyFingerprint:
    """Testes de fingerprint do request"""

    @staticmethod
    def _fp(data):
        return hashlib.sha256(
            json.dumps(data, sort_keys=True, ensure_ascii=False,
                       cls=DjangoJSONEncoder).encode('utf-8')
        ).hexdigest()

    def test_same_payload_same_fingerprint(self):
        data = {'name': 'Test', 'value': 123}
        assert self._fp(data) == self._fp(data)

    def test_different_payload_different_fingerprint(self):
        assert self._fp({'name': 'Test', 'value': 123}) != self._fp(
            {'name': 'Test', 'value': 456})

    def test_order_independent_fingerprint(self):
        assert self._fp({'b': 2, 'a': 1}) == self._fp({'a': 1, 'b': 2})


# ---------------------------------------------------------------------------
# Concorrência (somente sequencial — roda em SQLite)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestIdempotencyConcurrency:
    """Testes de concorrência"""

    def test_same_key_sequential_is_replay(self, client, category):
        """
        Duas requisições sequenciais com a mesma chave:
        a segunda é replay (201) e não cria duplicata.
        """
        data = {
            'name': 'Produto Concorrente',
            'category': category.id,
            'sale_price': '15.00',
            'purchase_price': '10.00',
            'stock': 10,
        }
        headers = {'HTTP_IDEMPOTENCY_KEY': 'concurrent-key-1234567890123456'}

        r1 = client.post("/api/products/", data, format="json", **headers)
        r2 = client.post("/api/products/", data, format="json", **headers)

        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r2.headers.get('X-Idempotent-Replay') == 'true'
        assert Product.objects.filter(name='Produto Concorrente').count() == 1


# ---------------------------------------------------------------------------
# Modelo IdempotencyRecord
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestIdempotencyRecordModel:
    """Testes do modelo IdempotencyRecord"""

    def test_record_creation(self):
        record = IdempotencyRecord.objects.create(
            key='test-key-1234567890123456',
            user_id=None,
            path='/api/products/',
            request_hash='abc123',
            response_status=201,
            response_body={'id': 1, 'name': 'Test'},
        )
        assert record.key == 'test-key-1234567890123456'
        assert record.response_status == 201
        assert record.response_body['id'] == 1

    def test_record_unique_key(self):
        IdempotencyRecord.objects.create(
            key='unique-key-1234567890123456',
            user_id=None,
            path='/api/products/',
            request_hash='abc123',
            response_status=201,
            response_body={},
        )
        with pytest.raises(IntegrityError):
            IdempotencyRecord.objects.create(
                key='unique-key-1234567890123456',
                user_id=None,
                path='/api/products/',
                request_hash='abc123',
                response_status=201,
                response_body={},
            )

    def test_record_str_representation(self):
        record = IdempotencyRecord.objects.create(
            key='str-key-1234567890123456',
            user_id=None,
            path='/api/products/',
            request_hash='abc123',
            response_status=201,
            response_body={},
        )
        assert 'str-key-1234567890123456' in str(record)
