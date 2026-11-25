import pytest
from rest_framework.test import APIClient


@pytest.mark.parametrize('path', ['/health', '/health/', '/api/health/'])
def test_health_publico(path, settings, monkeypatch):
    settings.REQUIRE_AUTH = True
    monkeypatch.setenv('RENDER_GIT_COMMIT', 'commit-teste')
    response = APIClient().get(path)
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
    assert response['X-Comercializa-Revision'] == 'commit-teste'
