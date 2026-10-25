import pytest
from pydantic import ValidationError
from app import main
from app.config import Settings


@pytest.mark.parametrize('host', ['localhost', '127.0.0.1', '[::1]'])
@pytest.mark.parametrize('port', [5173, 8000])
def test_development_loopback_guest_and_csrf(client, monkeypatch, host, port):
    monkeypatch.setattr(main.settings, 'app_env', 'development')
    monkeypatch.setattr(main.settings, 'public_origin', 'http://localhost:5173')
    headers = {'Origin': f'http://{host}:{port}', 'Sec-Fetch-Site': 'same-origin'}
    response = client.post('/api/v1/guest', json={}, headers=headers)
    assert response.status_code == 200, response.text
    headers['X-CSRF-Token'] = response.json()['csrf_token']
    assert client.post('/api/v1/export', json={}, headers=headers).status_code == 200
    headers['X-CSRF-Token'] = 'wrong'
    assert client.post('/api/v1/export', json={}, headers=headers).status_code == 403


@pytest.mark.parametrize('origin', [
    'https://evil.example',
    'http://localhost.evil.example:5173',
    'http://127.0.0.1.evil.example:5173',
    'http://127.0.0.2:5173',
    'http://localhost:5174',
    'https://localhost:5173',
    'null',
])
def test_development_rejects_unlisted_origins(client, origin):
    response = client.post('/api/v1/guest', json={}, headers={
        'Origin': origin,
        'Host': 'localhost:5173',
        'X-Forwarded-Host': 'localhost:5173',
        'X-Forwarded-Proto': 'http',
    })
    assert response.status_code == 403
    assert response.json()['error']['code'] == 'origin_rejected'
    assert main.settings.public_origin in response.json()['error']['message']


def test_missing_origin_and_cross_site_still_rejected(client):
    client.headers.pop('Origin')
    assert client.post('/api/v1/guest', json={}).status_code == 403
    assert client.post('/api/v1/guest', json={}, headers={
        'Origin': 'http://127.0.0.1:5173', 'Sec-Fetch-Site': 'cross-site',
    }).status_code == 403


def test_production_has_no_development_aliases(client, monkeypatch):
    monkeypatch.setattr(main.settings, 'app_env', 'production')
    monkeypatch.setattr(main.settings, 'public_origin', 'https://fluid.example')
    assert main.settings.allowed_origins == frozenset({'https://fluid.example'})
    for origin in ['http://localhost:5173', 'http://127.0.0.1:8000', 'https://fluid.example.evil.test']:
        assert client.post('/api/v1/guest', json={}, headers={'Origin': origin}).status_code == 403
    assert client.post('/api/v1/export', json={}, headers={'Origin': 'https://fluid.example'}).status_code == 200


def test_custom_development_origin_stays_exact():
    settings = Settings(app_env='development', public_origin='https://preview.example/')
    assert settings.allowed_origins == frozenset({'https://preview.example'})


def test_configured_loopback_port_and_url_normalization():
    settings = Settings(app_env='development', public_origin='http://LOCALHOST:9000/')
    assert settings.public_origin == 'http://localhost:9000'
    assert 'http://127.0.0.1:9000' in settings.allowed_origins
    assert 'http://localhost:9001' not in settings.allowed_origins
    assert Settings(public_origin='https://FLUID.example:443/').public_origin == 'https://fluid.example'


@pytest.mark.parametrize('origin', [
    'null', 'file:///tmp/page.html', 'https://fluid.example/path',
    'https://owner:password@fluid.example', 'https://fluid.example?key=bad',
    'https://fluid.example#fragment', 'http://localhost:0', 'http://localhost:99999',
])
def test_invalid_public_origin_configuration_fails(origin):
    with pytest.raises(ValidationError):
        Settings(public_origin=origin)
