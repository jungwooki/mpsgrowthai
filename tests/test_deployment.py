"""Regression checks for GitHub deployments without local reference originals."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from backend import server


def test_index_alias_and_assets():
    client = TestClient(server.app)
    assert client.get('/index.html').content == client.get('/').content
    for path in ['/frontend/js/app.js', '/frontend/js/clinical-report.js',
                 '/frontend/js/memo-parser.js', '/frontend/css/styles.css',
                 '/frontend/css/workspace.css', '/frontend/assets/mps-symbol.png']:
        assert client.get(path).status_code == 200


def test_missing_originals_do_not_crash_basic_or_ai_evaluation(monkeypatch, tmp_path):
    monkeypatch.setattr(server, 'ROOT', tmp_path)
    monkeypatch.setenv('OPENAI_API_KEY', 'test-only')
    client = TestClient(server.app)
    status = client.get('/api/status').json()
    assert status['references_ready'] is False
    assert len(status['missing_sources']) == len(server.MANIFEST)
    assert all(not item['available'] for item in client.get('/api/library').json())
    assert client.get('/api/sources/R01').status_code == 503
    patient = dict(sex=1, birth='2014-01-01', exam='2026-01-01', height=150)
    basic = client.post('/api/evaluate', data={'patient': json.dumps(patient)})
    assert basic.status_code == 200 and basic.json()['metrics']['height']['available']
    patient.update(use_ai=True, consent=True)
    result = client.post('/api/evaluate', data={'patient': json.dumps(patient)})
    assert result.status_code == 200
    assert result.json()['ai'] is None
    assert '근거 원본' in result.json()['ai_error']


def test_vercel_limits_before_processing(monkeypatch):
    monkeypatch.setenv('VERCEL', '1')
    client = TestClient(server.app)
    assert client.get('/api/status').json()['upload_limit_bytes'] == 4_000_000
    result = client.post('/api/evaluate', content=b'', headers={'content-length': '4500000'})
    assert result.status_code == 413
    assert '4MB' in result.json()['detail']


def test_vercel_large_original_has_actionable_error(monkeypatch, tmp_path):
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setattr(server, 'ROOT', tmp_path)
    folder = tmp_path / 'data/sources'
    folder.mkdir(parents=True)
    (folder / server.SOURCES['R01']['name']).write_bytes(b'0' * 4_000_001)
    response = TestClient(server.app).get('/api/sources/R01')
    assert response.status_code == 413
    assert '다운로드 한도' in response.json()['detail']


def test_lambda_library_uses_private_urls_for_pdf_and_spreadsheets(monkeypatch):
    from unittest.mock import Mock
    monkeypatch.setenv('AWS_LAMBDA_FUNCTION_NAME','growthai')
    monkeypatch.setenv('MEDIA_S3_BUCKET','private-test')
    storage=Mock()
    storage.generate_presigned_url.return_value='https://private-test.s3.example/signed'
    monkeypatch.setattr(server.media_storage,'request_client',lambda request:storage)
    client=TestClient(server.app)
    for source,kind in [('R01','inline'),('R05','attachment')]:
        r=client.get('/api/sources/'+source,follow_redirects=False)
        assert r.status_code==302
        options=storage.generate_presigned_url.call_args.kwargs
        assert options['Params']['Key'].startswith('references/'+source)
        assert options['Params']['ResponseContentDisposition'].startswith(kind)
        assert options['ExpiresIn']==300
    assert storage.close.call_count==2


def test_library_missing_s3_object_shows_actionable_error(monkeypatch):
    from unittest.mock import Mock
    from botocore.exceptions import ClientError
    monkeypatch.setenv('AWS_LAMBDA_FUNCTION_NAME','growthai')
    monkeypatch.setenv('MEDIA_S3_BUCKET','private-test')
    storage=Mock()
    storage.head_object.side_effect=ClientError({'Error':{'Code':'404'}},'HeadObject')
    monkeypatch.setattr(server.media_storage,'request_client',lambda request:storage)
    r=TestClient(server.app).get('/api/sources/R01')
    assert r.status_code==503 and '자료실 원본 연결' in r.json()['detail']
    storage.generate_presigned_url.assert_not_called()
    storage.close.assert_called_once()


def test_deployment_guard_skips_missing_or_corrupt_private_originals(tmp_path):
    import hashlib
    import subprocess
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root/'vercel.json').read_text())
    command = config['ignoreCommand']
    # Older Git commits without the checker must also preserve live production.
    assert subprocess.run(command, shell=True, cwd=tmp_path, capture_output=True).returncode == 0
    (tmp_path/'scripts').mkdir()
    (tmp_path/'scripts/check_references.cjs').write_bytes((root/'scripts/check_references.cjs').read_bytes())
    (tmp_path/'data/sources').mkdir(parents=True)
    payload = b'reference fixture'
    manifest = [dict(name=f'{i}.pdf', size=len(payload), sha256=hashlib.sha256(payload).hexdigest()) for i in range(11)]
    (tmp_path/'data/manifest.json').write_text(json.dumps(manifest))
    assert subprocess.run(command, shell=True, cwd=tmp_path, capture_output=True).returncode == 0
    for source in manifest:
        (tmp_path/'data/sources'/source['name']).write_bytes(payload)
    assert subprocess.run(command, shell=True, cwd=tmp_path, capture_output=True).returncode == 1
    (tmp_path/'data/sources/0.pdf').write_bytes(b'wrong')
    assert subprocess.run(command, shell=True, cwd=tmp_path, capture_output=True).returncode == 0


def test_docker_includes_all_application_pages():
    root = Path(__file__).resolve().parents[1]
    dockerfile = (root / 'Dockerfile').read_text()
    allow = (root / '.dockerignore').read_text().splitlines()
    assert 'FROM python:3.12-slim' in dockerfile
    for page in ('index.html', 'workspace.html', 'headquarters.html'):
        assert root.joinpath(page).is_file()
        assert '!' + page in allow
        assert page in next(line for line in dockerfile.splitlines() if line.startswith('COPY server.py'))
