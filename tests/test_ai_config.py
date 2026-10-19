import pytest
from backend.ai_config import model_name
from backend import server
from fastapi.testclient import TestClient


@pytest.mark.parametrize('value', [None, '', ' ', '\r\n\t'])
def test_empty_model_uses_default(monkeypatch, value):
    if value is None:
        monkeypatch.delenv('OPENAI_MODEL', raising=False)
    else:
        monkeypatch.setenv('OPENAI_MODEL', value)
    assert model_name() == 'gpt-4.1'
    assert TestClient(server.app).get('/api/status').json()['model'] == 'gpt-4.1'


def test_explicit_model_is_preserved_and_trimmed(monkeypatch):
    monkeypatch.setenv('OPENAI_MODEL', ' gpt-4.1-2025-04-14\r\n')
    assert model_name() == 'gpt-4.1-2025-04-14'
