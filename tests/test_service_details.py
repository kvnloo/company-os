"""Consumer tests for real owner GET schemas; fixtures never mean live data."""
import json
from test_projection import api
from test_live_api import source_server


def test_existing_bridge_capabilities_are_visible_without_becoming_authority(monkeypatch):
    payload = {'schema':'agentweb.z0.bridge.capabilities.v1',
        'bridge_protocol_versions':['agentweb.z0.bridge.v1', 'PRIVATE_SENTINEL'],
        'transport':{'max_active':4, 'max_request_bytes':40000, 'socket_backlog':8,
                     'queue_policy':'reject_excess', 'overload_status':503},
        'active_dispatch_supported':True,
        'endpoints':[{'path':'/v1/plan','kind':'plan','modes':['shadow'], 'physical_execution':False},
                     {'path':'/v1/experimental/choice','kind':'decide','modes':['shadow'], 'physical_execution':True},
                     {'path':'PRIVATE_SENTINEL','secret':'PRIVATE_SENTINEL'}]}
    with source_server({'/v1/bridge/capabilities':payload}) as (url, requests):
        monkeypatch.setenv('COMPANY_OS_Z0_URL',url)
        data,sources=api._z0_live()
    bridge=data.get('bridge_capabilities')
    assert bridge is not None, 'Existing capability GET must be wired'
    assert bridge['transport']['max_active']==4
    assert bridge['endpoints'][1]['physical_execution'] is True  # shadow can call a model
    assert bridge['execution_permission'] is False
    assert 'PRIVATE_SENTINEL' not in json.dumps([data,sources])
    assert sources['z0_bridge']['endpoint']=='/v1/bridge/capabilities'
    assert sources['z0_bridge']['observed_at'] is None
    assert all(method=='GET' for method,_,_ in requests)


def test_owner_outcome_windows_and_review_gates_keep_evidence_freshness_unknown(monkeypatch):
    coverage = {'schema':'z0int.agentweb_outcome_coverage.v1', 'as_of':'2026-10-10T20:00:00Z',
        'expectations':2, 'observations':1, 'required_windows':['1h'],
        'by_window':{'1h':{'eligible':2,'observed':1,'missing':1,'coverage':0.5,
                         'complete_coverage':None,'passes':False,'reasons':['joined_coverage_below_threshold']},
                     '24h':{'eligible':0,'coverage':None}},
        'promotion_gate':{'eligible':False,'causal_quality_proven':False,'necessary_not_sufficient':True,
                          'reasons':['1h:joined_coverage_below_threshold']}}
    randomized = {'schema':'z0int.agentweb_randomized_outcome_evidence.v1', 'as_of':coverage['as_of'],
        'experiments':{'PRIVATE_SENTINEL':{'registered_assignments':4,'valid_randomized_assignments':3,
            'arms':{'candidate':{'units':2,'treatment_hashes':['PRIVATE_SENTINEL']},'reference':{'units':1}},
            'review_ready':True,'human_review_required':True,'auto_promotion_allowed':False,
            'causal_quality_proven':False, 'reasons':['minimum_live_sample_not_met','PRIVATE_SENTINEL']}},
        'review_ready_any':True,'human_review_required':True,'auto_promotion_allowed':False,'causal_quality_proven':False}
    with source_server({'/v1/observe/outcome/coverage':coverage,
                        '/v1/observe/outcome/randomized-evidence':randomized}) as (url, requests):
        monkeypatch.setenv('COMPANY_OS_Z0_URL',url)
        data,sources=api._z0_live()
    windows=data['outcome_coverage'].get('by_window')
    assert windows is not None, 'Do not discard existing source-owned coverage denominators'
    assert windows['1h']['missing']==1 and windows['24h']['coverage'] is None
    assert data['outcome_coverage']['promotion_gate']['reasons']==['1h:joined_coverage_below_threshold']
    review=data['randomized_evidence']
    assert review['review_ready_any'] is True and review['auto_promotion_allowed'] is False
    assert review['experiments'][0]['experiment_ref'].startswith('ref-')
    assert review['experiments'][0]['arms']['reference']['units']==1
    assert 'PRIVATE_SENTINEL' not in json.dumps([data,sources])
    assert sources['z0_outcomes']['observed_at'] is None  # as_of is assessment, not last event
    assert sources['z0_outcomes']['assessed_at'] is not None
    assert sources['z0_evaluation']['coverage']['scope']=='agentweb_registered_experiments_only'


def test_existing_cluster_aggregate_is_separate_from_authority_and_global_work(monkeypatch):
    assert callable(getattr(api,'_cluster_live',None)), 'existing cluster status GET needs an isolated consumer'
    payload={'cluster_id':'PRIVATE_SENTINEL','version':'python-1.0.0','node_count':1,'online_nodes':1,
             'task_count':0,'tasks_by_status':{'pending':0,'ready':0,'running':0,'completed':0,'failed':0},
             'uptime_seconds':4,'private':'PRIVATE_SENTINEL'}
    with source_server({'/api/v1/cluster/status':payload}) as (url,requests):
        monkeypatch.setenv('COMPANY_OS_CLUSTER_URL',url)
        data,source=api._cluster_live()
    assert data['task_count']==0 and data['tasks_by_status']['running']==0
    assert data['cluster_ref'].startswith('ref-')
    assert 'PRIVATE_SENTINEL' not in json.dumps([data,source])
    assert source['observed_at'] is None and source['coverage']['scope']=='hermes_cluster_registry_only'
    assert source['coverage']['unreported_task_states']=='unknown'
    assert requests[0][0:2]==('GET','/api/v1/cluster/status') and len(requests)==1


def test_cluster_is_opt_in_and_rejects_nonlocal_origins_without_requests(monkeypatch):
    assert callable(getattr(api,'_cluster_live',None))
    monkeypatch.delenv('COMPANY_OS_CLUSTER_URL',raising=False)
    assert api._cluster_live()[1]['reason']=='not_configured'
    monkeypatch.setattr(api,'_get_readonly',lambda *a: (_ for _ in ()).throw(AssertionError('must not fetch')))
    for url in ('https://example.org','http://example.org','http://8.8.8.8','http://127.0.0.1/config',
                'http://name:password@127.0.0.1:8787','http://127.0.0.1:8787?secret=x'):
        monkeypatch.setenv('COMPANY_OS_CLUSTER_URL',url)
        assert api._cluster_live()[1]['reason']=='invalid_local_origin'


def test_live_projection_reports_limits_instead_of_silent_truncation(monkeypatch):
    metrics='\n'.join(f'z0intelligence_provider_error_total{{provider="groq",status="{n}"}} 0' for n in range(100,170))
    bridge={'schema':'agentweb.z0.bridge.capabilities.v1','endpoints':[{'path':'/v1/plan'}]*70}
    with source_server({'/metrics':metrics,'/v1/bridge/capabilities':bridge}) as (url,requests):
        monkeypatch.setenv('COMPANY_OS_Z0_URL',url)
        data,sources=api._z0_live()
    for source in ('z0_metrics','z0_bridge'):
        cov=sources[source]['coverage']
        assert isinstance(cov,dict), 'bounded rows need explicit coverage'
        assert cov['returned']==64 and cov['total']==70 and cov['truncated'] is True
    assert len(data['metrics'])==64


def test_overloaded_metrics_are_unavailable_not_a_measured_empty_inventory(monkeypatch):
    with source_server({'/metrics':(503,'')}) as (url,requests):
        monkeypatch.setenv('COMPANY_OS_Z0_URL',url)
        data,sources=api._z0_live()
    assert 'metrics' not in data, 'empty overload body must not become zero observed counters'
    assert sources['z0_metrics']['status']=='unavailable'
