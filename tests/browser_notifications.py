"""Exercise opt-in UI against mocked private service; no real email is sent."""
import json,sys
from playwright.sync_api import sync_playwright,expect
state={'requests':[]}
def route_api(route):
    if route.request.url.endswith('/api/notification-config'):data={'api_url':'https://notify.test'}
    elif route.request.url.endswith('/api/config'):data={'ready':True,'channel':'email'}
    elif route.request.url.endswith('/api/subscribe'):
        data=route.request.post_data_json;state['requests'].append(data)
        assert data['consent'] is True;assert data['email']=='fan@example.com';assert data['preferences']['section']=='F4';assert data['preferences']['row']==12;assert data['preferences']['seat_mask']=='1X';assert data['preferences']['cadence']=='updates';assert data['preferences']['min_percent']==10
        data={'ok':True}
    else:route.continue_();return
    route.fulfill(status=200,content_type='application/json',body=json.dumps(data),headers={'Access-Control-Allow-Origin':'*'})
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':390,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('**/api/notification-config',route_api);page.route('https://notify.test/**',route_api)
    page.goto(sys.argv[1]+'/#notifications');expect(page.locator('#notify-email')).to_be_enabled(timeout=15000);expect(page.locator('#notifications-view')).to_be_visible();assert page.locator('#explorer-view').is_hidden()
    page.fill('#notify-email','fan@example.com');page.select_option('#notify-section','F4');page.fill('#notify-row','12');page.select_option('#notify-mask','1X')
    page.locator('#notify-submit').click();assert not state['requests'],'Consent must be explicit';page.check('#notify-consent');page.locator('#notify-submit').click();expect(page.locator('#notify-status')).to_contain_text('not active until you confirm');assert len(state['requests'])==1
    assert 'fan@example.com' not in page.evaluate('JSON.stringify(localStorage)');expect(page.locator('#notify-email')).to_have_value('')
    page.select_option('#language','zh');expect(page.locator('#notify-title')).to_have_text('订阅匹配票源提醒');expect(page.locator('#notify-status')).to_contain_text('确认邮箱前不会启用')
    for width in [320,390,750,1100,1440]:
        page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
    assert not errors,errors;browser.close();print('Email signup browser passed: preferences, consent, confirmation-only success, private email handling, Mandarin, persistent tab and mobile layout.')
