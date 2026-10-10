"""Display identity regressions use explicitly labelled browser-only fixture rows."""
import copy
import json
import time
from test_design_chooser import browser, chooser_url, open_live, API
from test_integrated_interactions import refresh, raw_detail


def test_same_pod_name_in_distinct_namespaces_inspects_the_clicked_identity(chooser_url,browser):
    page=browser.new_page()
    live=open_live(page,chooser_url)
    fixture=copy.deepcopy(live)
    fixture['generated_at']=time.time()
    fixture['k8s']['pods']=[{'name':'ref-test-same','namespace':ns,'phase':'Running',
                           'workload_ready':False,'ready':0,'containers':1,'restarts':0}
                          for ns in ('ref-test-first','ref-test-second')]
    page.route('**'+API+'snapshot',lambda route:route.fulfill(json=fixture))
    refresh(page)
    page.locator('.k8s-list button').nth(1).click()
    assert raw_detail(page)['namespace']=='ref-test-second'
    assert page.locator('#inspect-title').get_attribute('data-node-id')=='pod:ref-test-second:ref-test-same'
    page.close()
