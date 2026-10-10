"""Production-importing truth-boundary tests; never use live providers."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('company_os_api', ROOT / 'hermes-plugin/dashboard/plugin_api.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


def test_process_presence_parses_multiword_comm_and_rejects_substrings(monkeypatch):
    raw = '32665 omp daemon brok 91\n1 pipewire 4\n2 kcompactd0 5\n3 acpi 5\n4 pi 0\nbad omp 5\n8 hermes nope\n9 claude -1\n'
    monkeypatch.setattr(api.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout=raw))
    rows = api._process_fleet()
    assert [r['pid'] for r in rows] == [32665, 4]
    assert [r['age_s'] for r in rows] == [91, 0]
    assert all(r['status'] == 'observed' and r['governed'] is None for r in rows)
    assert all(r['heartbeat_at'] is None and r['session_id'] is None for r in rows)
    assert rows[0]['name'] == 'omp'


def test_unjoined_receipts_never_become_live_fleet_or_economics(monkeypatch):
    rows = [{'ts': 100, 'trace_id': 'dispatch-1', 'input_tokens': 9,
             'cost_usd': 2, 'extra': {'admission_token': 'private-token'},
             'outcome': {'verified_success': True}}] * 3
    monkeypatch.setattr(api, '_process_fleet', lambda: [])
    assert api._fleet({'fleet': [{'name': 'PRIVATE_SENTINEL'}]}, rows) == []
    economics = api._economics(rows)
    for key in ('input_tokens', 'output_tokens', 'cached_input_tokens',
                'actual_tokens', 'observed_cost_usd', 'verified_events', 'governed_events'):
        assert economics[key] is None
    assert economics['reason'] == 'tokenomics_read_contract_missing'


def test_snapshot_and_health_isolate_failure_and_do_not_read_unqualified_data(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    forbidden_reads = []
    def forbidden(*args, **kwargs):
        forbidden_reads.append(True)
        raise RuntimeError('unqualified receipt/control/quota/DB read')
    def broken():
        raise UnicodeError('PRIVATE_SENTINEL /home/private')
    for name in ('_receipt_rows', '_z0_control', '_quota', '_agentsview'):
        monkeypatch.setattr(api, name, forbidden, raising=False)
    monkeypatch.setattr(api, '_z0_capacity', broken)
    monkeypatch.setattr(api, '_process_fleet', lambda: [])
    monkeypatch.setattr(api, '_k8s', lambda: ({'available': True, 'pods': [], 'nodes': []}, {'status': 'ok'}))
    monkeypatch.setattr(api, '_z0_live', lambda: ({}, {}), raising=False)
    monkeypatch.setattr(api, '_host_metadata', lambda: ({}, {}))
    app = FastAPI()
    app.include_router(api.router, prefix='/api/plugins/company-os')
    with TestClient(app, raise_server_exceptions=False) as client:
        snapshot = client.get('/api/plugins/company-os/snapshot')
        assert snapshot.status_code == 200
        s = snapshot.json()
        assert s['sources']['z0_capacity']['status'] == 'unavailable'
        assert s['sources']['k8s']['status'] == 'ok'
        assert s['economics']['observed_cost_usd'] is None
        assert s['flow'] == [] and s['control']['available'] is False
        assert s['coverage']['scope'] == 'local_partial'
        assert len(s['implementation']['content_sha256']) == 64
        assert 'PRIVATE_SENTINEL' not in snapshot.text and '/home/private' not in snapshot.text
        assert client.get('/api/plugins/company-os/health').status_code == 200
        for method in ('post', 'put', 'delete'):
            assert getattr(client, method)('/api/plugins/company-os/snapshot').status_code == 405
    assert forbidden_reads == []


def test_capacity_recursive_privacy_bounds_and_freshness(monkeypatch, tmp_path):
    import json
    now = 1800000000
    monkeypatch.setattr(api, '_now', lambda: now)
    secret = 'PRIVATE_SENTINEL sk-test-inert /home/private prompt contents'
    raw = {'schema': api.CAPACITY_SCHEMA, 'generated_at': now, 'observed_at': now - 500,
           'sources': {'tern': {'status': 'ok', 'observed_at': now - 500, 'detail': secret}, secret: {'secret': secret}},
           'hosts': [{'host_id': secret, 'label': secret, 'rtt_ms': {'secret': secret},
                      'resources': {'cpu_logical': secret, 'ram_available_bytes': 0,
                                    'gpus': [{'name': secret, 'id': secret, 'memory_free_bytes': 0}]},
                      'observed_at': now - 500}] * 100,
           'sessions': [{'session_id': 0, 'name': secret, 'migration_allowed': True,
                         'session_sticky': False, 'locked': False, 'tab_count': 0}],
           'offers': [{'offer_id': secret, 'provider': secret, 'model': secret, 'price': {'secret': secret},
                       'observed_at': now - 500, 'quota': {'remaining': None, 'limit': 0,
                       'dimensions': {'tokens': {'remaining': 7, 'limit': 9, 'reset_at': now - 1}, secret: {'source': secret}}}}],
           'leases': [{'placement_id': secret, 'selection_reason': secret}]}
    path = tmp_path / 'capacity.json'
    path.write_text(json.dumps(raw))
    monkeypatch.setenv('COMPANY_OS_Z0_CAPACITY_SNAPSHOT', str(path))
    projection, source = api._z0_capacity()
    text = json.dumps([projection, source], allow_nan=False)
    assert 'PRIVATE_SENTINEL' not in text and 'sk-test-inert' not in text and '/home/private' not in text
    assert len(projection['hosts']) == 64
    assert projection['coverage']['truncated'] is True
    assert source['freshness'] == 'stale' and source['observed_at'] == now - 500
    assert source['source_version'].startswith('sha256:')
    assert projection['hosts'][0]['resources']['ram_available_bytes'] == 0
    assert projection['sessions'][0]['locked'] is False
    assert projection['sessions'][0]['tab_count'] == 0
    assert projection['sessions'][0]['migration_allowed'] is False
    assert projection['offers'][0]['quota']['dimensions']['tokens']['remaining'] is None
    assert projection['offers'][0]['quota']['limit'] == 0


@pytest.mark.parametrize('body', [b'\xff', b'{', b'[]', b'{"schema":"unsupported"}', b'x' * 600000], ids=['encoding', 'json', 'type', 'schema', 'oversize'])
def test_bad_capacity_is_only_a_missing_or_invalid_source(monkeypatch, tmp_path, body):
    path = tmp_path / 'bad.json'
    path.write_bytes(body)
    monkeypatch.setenv('COMPANY_OS_Z0_CAPACITY_SNAPSHOT', str(path))
    data, source = api._z0_capacity()
    assert data is None
    assert source['status'] in ('unavailable', 'degraded')
    assert source['freshness'] == 'unknown'


@pytest.mark.parametrize('observed, freshness', [(None, 'unknown'), (1800000050, 'invalid'), (1799999999, 'fresh')])
def test_capacity_generation_and_mtime_are_not_observation(monkeypatch, tmp_path, observed, freshness):
    import json
    monkeypatch.setattr(api, '_now', lambda: 1800000000)
    path = tmp_path / 'capacity.json'
    path.write_text(json.dumps({'schema': api.CAPACITY_SCHEMA, 'generated_at': 1800000000, 'observed_at': observed}))
    monkeypatch.setenv('COMPANY_OS_Z0_CAPACITY_SNAPSHOT', str(path))
    _, source = api._z0_capacity()
    assert source['freshness'] == freshness


def test_k8s_inventory_is_not_readiness_and_names_are_private(monkeypatch):
    pods = {'items': [{'metadata': {'name': 'PRIVATE_SENTINEL'}, 'spec': {'containers': [{}, {}]},
                      'status': {'phase': 'Running', 'conditions': [{'type': 'Ready', 'status': 'False'}],
                                 'containerStatuses': [{'ready': False, 'restartCount': 15}]}}]}
    nodes = {'items': [{'metadata': {'name': '/home/private'}, 'status': {}}]}
    monkeypatch.setattr(api.shutil, 'which', lambda name: '/usr/bin/kubectl')
    monkeypatch.setattr(api, '_run_json', lambda args: (pods if 'pods' in args else nodes, None))
    k8s, source = api._k8s()
    assert source['status'] == 'degraded'
    assert k8s['ready'] is False
    assert k8s['pods'][0]['workload_ready'] is False
    assert k8s['nodes'][0]['ready'] is None
    assert k8s['pods'][0]['restarts'] == 15
    assert 'PRIVATE_SENTINEL' not in str(k8s) and '/home/private' not in str(k8s)


def test_k8s_truncation_and_missing_counters_cannot_claim_readiness(monkeypatch):
    pods = {'items': [{'metadata': {}, 'status': {'phase': 'Running',
                      'conditions': [{'type': 'Ready', 'status': 'True'}],
                      'containerStatuses': [{'ready': True}]}}] * 65}
    nodes = {'items': [{'metadata': {}, 'status': {'conditions': [{'type': 'Ready', 'status': 'True'}]}}]}
    monkeypatch.setattr(api.shutil, 'which', lambda name: '/usr/bin/kubectl')
    monkeypatch.setattr(api, '_run_json', lambda args: (pods if 'pods' in args else nodes, None))
    data, source = api._k8s()
    assert data['ready'] is None
    assert data['coverage']['truncated'] is True
    assert source['status'] == 'degraded'
    assert data['pods'][0]['restarts'] is None


def test_process_command_failure_is_not_an_empty_healthy_fleet(monkeypatch):
    monkeypatch.setattr(api.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=1, stdout=''))
    with pytest.raises(RuntimeError):
        api._process_fleet()


def test_host_metadata_retains_disk_and_permission_checks_without_contents(monkeypatch, tmp_path):
    config = tmp_path / '.config/environment.d'
    config.mkdir(parents=True)
    secret_file = config / 'PRIVATE_SENTINEL.conf'
    secret_file.write_text('PRIVATE_SENTINEL credential')
    secret_file.chmod(0o666)
    monkeypatch.setattr(api.Path, 'home', lambda: tmp_path)
    monkeypatch.setattr(api.shutil, 'disk_usage', lambda path: SimpleNamespace(total=100, used=99, free=1))
    monkeypatch.setattr(api.Path, 'read_text', lambda *a, **k: (_ for _ in ()).throw(AssertionError('content read forbidden')))
    data, source = api._host_metadata()
    assert data['disks']['home']['status'] == 'critical'
    assert data['disks']['data']['free_bytes'] == 1
    assert data['security']['unsafe_count'] == 1
    assert data['security']['status'] == 'critical'
    assert source['status'] == 'degraded'
    assert 'PRIVATE_SENTINEL' not in str(data)
