"""Actual integrated browser acceptance; fault payloads are labelled consumer-only controls."""
import copy
import json
import time

from test_design_chooser import browser, chooser_url, open_live, ARTIFACTS, API
from test_integrated_chooser import GROUPS

LAYOUTS=[('spatial','Spatial cockpit'),('balanced','Operations split'),('dense','Instrument desk')]


def raw_detail(page):
    return json.loads(page.locator('#inspect-body .raw pre').text_content())


def refresh(page):
    with page.expect_response('**'+API+'snapshot') as response:
        page.get_by_role('button',name='Refresh snapshot',exact=True).click()
    assert response.value.status == 200
    page.wait_for_function("() => !document.querySelector('#refresh').disabled")
    return response.value.json()


def ready_snapshot(page,snapshot,required,label):
    # Diagnostic readiness only: never changes production polling or fabricates rows.
    attempts=[]
    for attempt in range(4):
        attempts.append({'generated_at':snapshot['generated_at'],
                         'sources':{k:snapshot['sources'][k]['status'] for k in required}})
        if all(snapshot['sources'][k]['status']=='ok' for k in required):
            break
        if attempt<3:
            time.sleep(2)  # bounded diagnostic backoff; do not hammer an overloaded producer
            snapshot=refresh(page)
    (ARTIFACTS/f'readiness-{label}.json').write_text(json.dumps(attempts,indent=2))
    assert all(snapshot['sources'][k]['status']=='ok' for k in required), attempts
    return snapshot


def test_six_live_layout_theme_inspections_paging_and_focus(chooser_url,browser):
    receipts=[]
    ARTIFACTS.mkdir(parents=True,exist_ok=True)
    for layout,title in LAYOUTS:
        for theme in ('dark','light'):
            page=browser.new_page(viewport={'width':1536,'height':1100})
            errors=[];requests=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.on('request',lambda r:requests.append({'method':r.method,'url':r.url}))
            snapshot=open_live(page,chooser_url)
            snapshot=ready_snapshot(page,snapshot,('z0_health','z0_bridge','z0_outcomes','z0_evaluation'),f'{layout}-{theme}')
            page.get_by_role('button',name='Pause updates',exact=True).click()
            page.get_by_role('tab',name=title,exact=True).click()
            page.get_by_role('button',name=theme.title(),exact=True).click()
            for group in GROUPS:
                page.get_by_role('button',name=f'Browse {group} group',exact=True).click()
                assert page.locator('#inspect-title').inner_text()==group
                assert page.locator('.detail-note').inner_text()
                assert page.locator('#provenance-summary').is_visible()
                assert page.locator('.child-list [data-child-id]').count()<=8
            page.get_by_role('button',name='Browse Services group',exact=True).focus()
            page.keyboard.press('ArrowRight')
            assert page.evaluate('document.activeElement.dataset.childId')=='service:health'
            page.keyboard.press('Enter')
            assert page.locator('#inspect-title').inner_text()=='Health'
            page.keyboard.press('ArrowLeft')
            page.get_by_role('button',name='Inspect Bridge capabilities',exact=True).click()
            bridge=raw_detail(page)
            assert bridge['schema']=='agentweb.z0.bridge.capabilities.v1'
            assert bridge['execution_permission'] is False
            page.get_by_role('button',name='Browse Evidence coverage group',exact=True).click()
            page.get_by_role('button',name='Inspect 1h outcome window',exact=True).focus()
            page.keyboard.press('Space')
            window=raw_detail(page)
            assert {'eligible','observed','complete','missing','coverage','passes'}<=window.keys()
            assert window['coverage'] is None or 0<=window['coverage']<=1
            page.get_by_role('button',name='Back one level',exact=True).click()
            assert page.evaluate('document.activeElement.dataset.childId')=='window:1h'
            page.get_by_role('button',name='Browse Evaluation group',exact=True).click()
            evaluation=raw_detail(page)
            assert evaluation['schema']=='z0int.agentweb_randomized_outcome_evidence.v1'
            assert evaluation['auto_promotion_allowed'] is False
            page.get_by_role('button',name='Browse Economics group',exact=True).click()
            assert raw_detail(page)['observed_cost_usd'] is None
            page.get_by_role('button',name='Browse Work & authority group',exact=True).click()
            page.get_by_role('button',name='Inspect Admission',exact=True).click()
            assert raw_detail(page)['state']=='unknown'
            page.get_by_role('button',name='Browse Cognition group',exact=True).click()
            page.get_by_role('button',name='Inspect Memory / reuse',exact=True).click()
            assert raw_detail(page)['runtime_usable'] is None
            page.get_by_role('button',name='Browse Sources & gaps group',exact=True).click()
            first_ids=page.locator('.child-list [data-child-id]').evaluate_all('(els)=>els.map(e=>e.dataset.childId)')
            page.get_by_role('button',name='Next children',exact=True).click()
            second_ids=page.locator('.child-list [data-child-id]').evaluate_all('(els)=>els.map(e=>e.dataset.childId)')
            assert not set(first_ids)&set(second_ids)
            assert len(set(first_ids+second_ids))==len(snapshot['sources'])
            child=page.locator('.child-list [data-child-id]').first
            identity=child.get_attribute('data-child-id')
            page.get_by_role('button',name='Resume updates',exact=True).click()
            page.wait_for_function("() => !document.querySelector('#refresh').disabled")
            child.focus()
            old=page.locator('#snapshot-time').inner_text()
            page.wait_for_function('(old)=>document.querySelector("#snapshot-time").textContent!==old',arg=old,timeout=25000)
            assert page.evaluate('document.activeElement.dataset.childId')==identity
            assert page.locator('.child-list [data-child-id]').evaluate_all('(els)=>els.map(e=>e.dataset.childId)')==second_ids
            page.keyboard.press('Enter')
            assert page.locator('#inspect-title').get_attribute('data-node-id')==identity
            page.locator('#provenance-summary').click()
            before=page.locator('#snapshot-time').inner_text()
            page.wait_for_function('(old)=>document.querySelector("#snapshot-time").textContent!==old',arg=before,timeout=25000)
            assert page.locator('#provenance-summary').evaluate('(el)=>el===document.activeElement')
            assert page.locator('.provenance').evaluate('(el)=>el.open')
            page.keyboard.press('Escape')
            assert page.evaluate('document.activeElement.dataset.childId')==identity
            page.get_by_role('button',name='Previous children',exact=True).click()
            assert page.locator('.child-list [data-child-id]').evaluate_all('(els)=>els.map(e=>e.dataset.childId)')==first_ids
            page.get_by_role('button',name='Collapse children',exact=True).click()
            refresh(page)
            assert page.get_by_role('button',name='Expand children',exact=True).is_visible()
            page.get_by_role('button',name='Expand children',exact=True).click()
            page.screenshot(path=str(ARTIFACTS/f'inspection-{layout}-{theme}.png'),full_page=True)
            assert not errors,errors
            assert all(r['method']=='GET' and r['url'].startswith(chooser_url) for r in requests)
            receipts.append({'layout':layout,'theme':theme,'groups':GROUPS,'paged_source_ids':first_ids+second_ids,
                             'poll_focus_id':identity,'bridge':bridge,'outcome_window':window,'evaluation':evaluation,
                             'errors':errors,'requests':requests})
            (ARTIFACTS/'integrated-browser-matrix.json').write_text(json.dumps(receipts,indent=2))
            page.close()
    assert len({(r['layout'],r['theme']) for r in receipts})==6


def test_latest_detail_and_provenance_survive_replacement_removal_and_source_failure(chooser_url,browser):
    page=browser.new_page(viewport={'width':1536,'height':1100})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    live=open_live(page,chooser_url)
    live=ready_snapshot(page,live,('z0_health','z0_providers'),'retention')
    assert live['z0_service']['providers'], 'requires actual observed provider row before fault controls'
    page.locator('.provider-list [data-provider]').first.click()
    initial=raw_detail(page)
    provider=initial['provider']
    current=copy.deepcopy(live)
    def fixture(route):
        current['generated_at']=time.time()
        route.fulfill(json=current)
    page.route('**'+API+'snapshot',fixture)
    row=next(p for p in current['z0_service']['providers'] if p['provider']==provider)
    row['inflight']=0;row['cap']=(initial['cap'] or 0)+1
    current['sources']['z0_providers']['source_version']='consumer-test-fixture:latest'
    refresh(page)
    latest=raw_detail(page)
    assert latest['inflight']==0 and latest['cap']==row['cap']
    page.locator('#raw-summary').click()
    current['z0_service']['providers']=[p for p in current['z0_service']['providers'] if p['provider']!=provider]
    refresh(page)
    assert raw_detail(page)==latest
    assert 'Disappearance is not completion' in page.locator('.detail-stale').inner_text()
    assert page.locator('.raw').evaluate('(el)=>el.open')
    page.locator('#provenance-summary').click()
    assert 'consumer-test-fixture:latest' in page.locator('.provenance').inner_text()
    page.screenshot(path=str(ARTIFACTS/'retained-latest-detail.png'),full_page=True)
    page.get_by_role('button',name='Browse Services group',exact=True).click()
    page.get_by_role('button',name='Inspect Health',exact=True).click()
    healthy=raw_detail(page)
    current['z0_service'].pop('health',None)
    current['sources']['z0_health'].update(status='unavailable',reason='read_failed')
    refresh(page)
    assert raw_detail(page)==healthy
    assert 'Selected source unavailable' in page.locator('.detail-stale').inner_text()
    page.unroute('**'+API+'snapshot')
    page.route('**'+API+'snapshot',lambda route:route.fulfill(status=503,body=''))
    page.get_by_role('button',name='Refresh snapshot',exact=True).click()
    page.wait_for_function("() => document.querySelector('#workspace').dataset.transport==='stale'")
    assert raw_detail(page)==healthy
    assert 'last-known' in page.locator('#outage-banner').inner_text()
    assert not errors,errors
    (ARTIFACTS/'retained-detail-receipt.json').write_text(json.dumps({'scope':'explicit consumer-only fault controls after real live read','provider':provider,'initial':initial,'latest':latest,'retained':True,'partial_source_failure':True,'http503':True,'errors':errors},indent=2))
    page.close()
