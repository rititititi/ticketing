"""Browser flow against mocked job responses; Worker security is tested separately in worker_admin.mjs."""
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
url=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:5012'
state={'signed_in':False,'published':False,'uploaded':False}
job='a'*32
rows=[dict(section='F4',row='12',seat_as_printed='1X',price=3500,sold=False,performance_date='2027-01-15',notes='',raw_ocr='F4区12排1X 3500')]
def route_api(route):
    path=route.request.url.split('/api/')[1]
    status=200;data={}
    if path=='session':status=200 if state['signed_in'] else 401;data={'csrf':'test-csrf'} if state['signed_in'] else {'error':'Please sign in'}
    elif path=='login':state['signed_in']=True;data={'ok':True}
    elif path=='sources':data=[{'index':1,'name':'existing.jpg'}]
    elif path=='upload':
        assert b'base_source' in route.request.post_data_buffer
        state['uploaded']=True;status=202;data={'id':job}
    elif path==f'jobs/{job}/image':
        source=json.loads((ROOT/'data/catalog.json').read_text())['sources'][0]['source_file'];route.fulfill(status=200,content_type='image/jpeg',body=(ROOT/'static/sources'/source).read_bytes());return
    elif path==f'jobs/{job}/publish':
        body=route.request.post_data_json
        assert body['reviewed_all_rows'] is True
        assert len(body['rows'])==2
        assert body['rows'][0]['row']=='13'
        assert body['rows'][0]['sold'] is True
        assert body['rows'][1]['row']=='15/16/17'
        state['published']=True;status=202;data={'ok':True}
    elif path==f'jobs/{job}':data={'status':'published'} if state['published'] else {'status':'review','rows':rows,'width':600,'height':800}
    else:raise AssertionError(path)
    route.fulfill(status=status,content_type='application/json',body=json.dumps(data))
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':390,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('**/api/**',route_api)
    page.goto(url)
    page.fill('#password','test-only-password')
    page.locator('#login-form button').click()
    expect(page.locator('#workspace')).to_be_visible()
    page.select_option('#base-source','1')
    source=json.loads((ROOT/'data/catalog.json').read_text())['sources'][0]['source_file']
    page.set_input_files('#image',ROOT/'static/sources'/source)
    page.locator('#upload-form button').click()
    expect(page.locator('#review')).to_be_visible()
    assert state['uploaded']
    page.locator('#rows [data-key="row"]').fill('13')
    page.locator('#rows [data-key="sold"]').check()
    page.locator('#add-row').click()
    page.locator('#rows tr').nth(1).locator('[data-key="section"]').fill('F4')
    page.locator('#rows tr').nth(1).locator('[data-key="row"]').fill('15/16/17')
    page.locator('#publish').click()
    expect(page.locator('#message')).to_contain_text('First confirm')
    page.locator('#confirmed').check();page.locator('#publish').click()
    expect(page.locator('#message')).to_contain_text('Published to the repository')
    assert state['published'];assert not errors,errors
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    print('Admin browser passed: login, version selection, image upload, editable row/seat fields, sold checkbox, added range row, explicit review confirmation, publish status, and mobile layout (mocked GitHub job responses).')
    browser.close()
