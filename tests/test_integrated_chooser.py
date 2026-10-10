"""Integrated chooser tests: live reads separate from explicit fault fixtures."""
import json
from test_design_chooser import browser, chooser_url, open_live, ARTIFACTS

GROUPS = ['Agents', 'Services', 'Resources', 'Capacity', 'Work & authority',
          'Cognition', 'Evidence coverage', 'Evaluation', 'Economics', 'Sources & gaps']


def test_ten_adapter_groups_and_bounded_keyboard_navigation(chooser_url, browser):
    page = browser.new_page(viewport={'width':1536, 'height':1100})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    open_live(page, chooser_url)
    assert page.locator('.group-strip button').count() == 10
    for label in GROUPS:
        assert page.get_by_role('button', name=f'Browse {label} group', exact=True).is_visible()
    page.get_by_role('button', name='Browse Services group', exact=True).focus()
    page.keyboard.press('ArrowRight')
    assert page.locator('#inspect-title').inner_text() == 'Services'
    assert page.evaluate('document.activeElement.dataset.childId') == 'service:health'
    page.keyboard.press('ArrowRight')
    assert page.locator('#inspect-title').inner_text() == 'Health'
    page.keyboard.press('ArrowLeft')
    assert page.locator('#inspect-title').inner_text() == 'Services'
    assert page.evaluate('document.activeElement.dataset.childId') == 'service:health'
    page.keyboard.press('Escape')
    assert page.locator('#inspect-title').inner_text() == 'Network'
    assert page.evaluate('document.activeElement.dataset.childId') == 'services'
    assert page.locator('.child-list [data-child-id]').count() == 8
    page.get_by_role('button', name='Next children', exact=True).click()
    assert page.locator('.child-list [data-child-id]').count() == 2
    assert page.locator('#child-page').inner_text() == '9–10 of 10 projected children'
    page.get_by_role('button', name='Previous children', exact=True).click()
    assert page.locator('.child-list [data-child-id]').count() == 8
    assert not errors
    page.close()


def test_failed_process_source_never_renders_a_measured_zero(chooser_url, browser):
    import copy, time
    page=browser.new_page()
    live=open_live(page, chooser_url)
    fixture=copy.deepcopy(live)
    fixture['generated_at']=time.time()
    fixture['fleet']=[]
    fixture['sources']['processes'].update(status='unavailable', freshness='unknown', reason='source_failed')
    page.route('**/api/plugins/company-os/snapshot', lambda route: route.fulfill(json=fixture))
    page.get_by_role('button',name='Refresh snapshot',exact=True).click()
    page.wait_for_function("() => document.querySelector('.process-list').textContent.includes('No matched')")
    assert page.locator('.process-pane .pane-heading .hud-label').inner_text().lower() == 'unknown'
    page.get_by_role('button',name='Browse Agents group',exact=True).click()
    assert 'unknown process matches' in page.locator('#inspect-body').inner_text()
    page.close()
