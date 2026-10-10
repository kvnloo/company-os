"""Real loopback HTTP contract tests. Fake source only; production consumer."""
import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from test_projection import api

PATHS = ['/healthz', '/readyz', '/v1/providers', '/metrics', '/v1/observe/outcome/coverage',
         '/v1/bridge/capabilities', '/v1/observe/outcome/randomized-evidence']


@contextmanager
def source_server(overrides=None):
    requests = []
    bodies = {
        '/v1/bridge/capabilities': {'schema':'agentweb.z0.bridge.capabilities.v1','endpoints':[]},
        '/v1/observe/outcome/randomized-evidence': {'schema':'z0int.agentweb_randomized_outcome_evidence.v1','experiments':{}},
        '/healthz': {'ok': True},
        '/readyz': {'ok': True, 'authority_protocol_version': 3, 'governed_remote_enabled': False, 'governed_remote_ready': False, 'scope': 'PRIVATE_SENTINEL'},
        '/v1/providers': {'providers': {'groq': {'cap': 16, 'inflight': 0, 'available': True, 'reason': 'eligible_unprobed', 'held_tokens': ['PRIVATE_SENTINEL']}, 'PRIVATE_SENTINEL': {'cap': 3}}},
        '/metrics': 'z0intelligence_dispatch_new_total 0\nz0intelligence_provider_inflight{provider="groq"} 0\nz0intelligence_provider_error_total{provider="PRIVATE_SENTINEL",status="500"} 7\n',
        '/v1/observe/outcome/coverage': {'schema': 'z0int.agentweb_outcome_coverage.v1', 'as_of': '2026-10-10T18:00:00Z', 'expectations': 0, 'observations': 0, 'promotion_gate': {'eligible': False, 'causal_quality_proven': False, 'reasons': ['no_required_expectations', 'PRIVATE_SENTINEL']}},
    }
    bodies.update(overrides or {})
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            requests.append((self.command, self.path, dict(self.headers)))
            body = bodies.get(self.path, {})
            status,body = body if isinstance(body,tuple) else (200,body)
            raw = body if isinstance(body, bytes) else (body.encode() if isinstance(body, str) else json.dumps(body).encode())
            self.send_response(status)
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_snapshot_consumes_only_existing_read_routes_and_projects_typed_fields(monkeypatch):
    monkeypatch.setattr(api, '_k8s', lambda: ({}, {}))
    monkeypatch.setattr(api, '_process_fleet', lambda: [])
    monkeypatch.setattr(api, '_z0_capacity', lambda: (None, {}))
    monkeypatch.setattr(api, '_host_metadata', lambda: ({}, {}))
    with source_server() as (url, requests):
        monkeypatch.setenv('COMPANY_OS_Z0_URL', url)
        s = api.build_snapshot()
    assert [r[1] for r in requests] == PATHS
    assert all(method == 'GET' and 'Authorization' not in headers for method, _, headers in requests)
    assert s['z0_service']['readiness']['governed_remote_ready'] is False
    assert s['z0_service']['providers'][0]['inflight'] == 0
    assert len(s['z0_service']['providers']) == 1
    assert len(s['z0_service']['metrics']) == 2
    assert s['z0_service']['metrics'][0]['value'] == 0
    assert s['sources']['z0_health']['checked_at'] > 0
    assert s['sources']['z0_health']['observed_at'] is None
    assert s['sources']['z0_health']['producer_revision'] is None
    assert s['sources']['z0_health']['source_version'].startswith('sha256:')
    assert s['z0_service']['outcome_coverage']['promotion_gate']['eligible'] is False
    assert s['economics']['observed_cost_usd'] is None
    assert 'PRIVATE_SENTINEL' not in json.dumps(s)
    assert s['control']['available'] is False and s['flow'] == []


def test_live_source_decode_failure_does_not_hide_other_sources(monkeypatch):
    with source_server({'/healthz': b'\xff'}) as (url, requests):
        monkeypatch.setenv('COMPANY_OS_Z0_URL', url)
        data, sources = api._z0_live()
    assert len(requests) == len(PATHS)
    assert sources['z0_health']['status'] == 'unavailable'
    assert sources['z0_providers']['status'] == 'ok'
    assert data['providers'][0]['cap'] == 16


def test_remote_urls_and_credentials_are_not_used(monkeypatch):
    for url in ('https://example.com', 'http://user:pass@127.0.0.1:11501', 'http://127.0.0.1:11501/refresh'):
        monkeypatch.setenv('COMPANY_OS_Z0_URL', url)
        data, sources = api._z0_live()
        assert not data
        assert sources['z0_service']['reason'] == 'invalid_loopback_origin'
