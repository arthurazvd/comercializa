"""Garantias do deploy gratuito: health, bloqueio da API e criação de usuário."""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APIClient
import pytest


@pytest.mark.django_db
def test_health_nao_pede_token():
    response = APIClient().get('/api/health/')
    assert response.status_code == 200
    assert response.data == {'status': 'ok'}


@pytest.mark.django_db
def test_login_token_status_e_logout():
    get_user_model().objects.create_user(username='gerente', password='TesteFort3@Senha')
    client = APIClient()
    bad = client.post('/api/auth/login/', {'username': 'gerente', 'password': 'incorreta'})
    assert bad.status_code == 400
    ok = client.post('/api/auth/login/', {'username': 'gerente', 'password': 'TesteFort3@Senha'})
    assert ok.status_code == 200
    assert ok.data['token']
    client.credentials(HTTP_AUTHORIZATION=f"Token {ok.data['token']}")
    assert client.get('/api/auth/status/').data['authenticated'] is True
    assert client.post('/api/auth/logout/').status_code == 200
    assert client.get('/api/auth/status/').status_code == 401


@pytest.mark.django_db
def test_api_protegida_na_configuracao_de_producao():
    with override_settings(REQUIRE_AUTH=True):
        client = APIClient()
        for path in ['/api/products/', '/api/categories/', '/api/sales/',
                     '/api/stock-overview/', '/api/stock-export/',
                     '/api/reports/finance/', '/api/reports/finance/export/']:
            assert client.get(path).status_code == 401, path
        assert client.get('/api/auth/status/').data['authentication_required'] is True
        assert client.get('/api/health/').status_code == 200


@pytest.mark.django_db
def test_bootstrap_admin_idempotente(monkeypatch):
    monkeypatch.setenv('INITIAL_ADMIN_USERNAME', 'admin-teste')
    monkeypatch.setenv('INITIAL_ADMIN_PASSWORD', 'SenhaSuperForte!123')
    monkeypatch.setenv('INITIAL_ADMIN_EMAIL', 'admin@exemplo.com')
    call_command('bootstrap_admin')
    user = get_user_model().objects.get(username='admin-teste')
    assert user.is_superuser is True
    assert user.check_password('SenhaSuperForte!123')
    monkeypatch.setenv('INITIAL_ADMIN_PASSWORD', 'OutraSenhaForte!456')
    call_command('bootstrap_admin')
    user.refresh_from_db()
    assert user.check_password('SenhaSuperForte!123')
