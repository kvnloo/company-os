"""All three dashboard views remain available; legacy preferences are not discarded."""
import json
from test_design_chooser import browser, chooser_url, API


def test_legacy_default_view_and_theme_remain_compatible_without_eliminating_other_views(chooser_url,browser):
    page=browser.new_page()
    legacy={'schema':'companyos.design-choice.v1','scope':'local-design-preference','design':'dense','theme':'light',
            'chosen_at':'2026-10-10T00:00:00Z','production_changed':False,'style_base':'7da554116d096cdfc7a7fb77658da5eca80bd6e4'}
    page.add_init_script(f"localStorage.setItem('companyos.chooser.choice.v1',JSON.stringify({json.dumps(legacy)}));localStorage.setItem('companyos.chooser.theme','light')")
    page.goto(chooser_url+'/design-chooser/')
    page.wait_for_selector('[data-loaded="true"]')
    assert page.locator('#workspace').get_attribute('data-layout')=='dense'
    assert page.locator('html').get_attribute('data-hud-theme')=='light'
    assert page.get_by_role('tablist',name='Dashboard views',exact=True).is_visible()
    assert page.get_by_role('button',name='Save as default view',exact=True).is_visible()
    for key,title in [('spatial','Spatial cockpit'),('balanced','Operations split'),('dense','Instrument desk')]:
        page.get_by_role('tab',name=title,exact=True).click()
        assert page.locator('#workspace').get_attribute('data-layout')==key
        assert page.get_by_role('tab').count()==3
        assert json.loads(page.evaluate("localStorage.getItem('companyos.chooser.choice.v1')"))==legacy
    assert 'All three views remain available' in page.locator('#choice-state').inner_text()
    page.close()
