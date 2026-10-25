import importlib.util
from pathlib import Path
import httpx
import pytest

spec = importlib.util.spec_from_file_location('model_discovery', Path(__file__).resolve().parents[2] / 'scripts/list_ai_models.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_discovery_only_gets_models_and_preserves_gateway_id():
    calls = []
    def handler(request):
        calls.append(request)
        assert request.method == 'GET'
        assert str(request.url) == 'https://campus.example/api/models'
        assert request.headers['Authorization'] == 'Bearer synthetic-key'
        assert request.content == b''
        return httpx.Response(200, json={'data': [{'id': 'gateway/claude-opus-4-6', 'name': 'Claude Opus 4.6'}]})
    rows = module.list_models('https://campus.example/api/', 'synthetic-key', transport=httpx.MockTransport(handler))
    assert rows == [{'id': 'gateway/claude-opus-4-6', 'name': 'Claude Opus 4.6'}]
    assert len(calls) == 1


@pytest.mark.parametrize('code', [302, 401, 403, 429, 500])
def test_discovery_does_not_follow_redirects_or_echo_raw_errors(code):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(code, headers={'Location': 'https://login.example'}, text='synthetic-secret-key raw exception')
    with pytest.raises(module.ModelDiscoveryError) as error:
        module.list_models('https://campus.example/api', 'synthetic-secret-key', transport=httpx.MockTransport(handler))
    assert 'synthetic-secret-key' not in str(error.value)
    assert len(calls) == 1


def test_discovery_filters_untrusted_terminal_text_and_key_echo():
    data = {'data': [{'id': 'valid-opus', 'name': 'Opus'}, {'id': '\x1b[31mbad'}, {'id': 'synthetic-key'}, {'id': 'bad-name', 'name': 'synthetic-key'}]}
    rows = module.list_models('https://campus.example/api', 'synthetic-key', transport=httpx.MockTransport(lambda r: httpx.Response(200, json=data)))
    assert rows == [{'id': 'valid-opus', 'name': 'Opus'}]


def test_discovery_rejects_nonlocal_http():
    with pytest.raises(module.ModelDiscoveryError):
        module.list_models('http://campus.example/api', 'synthetic-key')
