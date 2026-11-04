"""Browser review flow with mocked authenticated API; security is tested in worker_admin.mjs."""
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
source=dict(source_index=121,source_file='4221793774750_.pic.jpg',width=911,height=756,sha256='source-hash',pages=1,total_rows=2,pending_rows=2)
record=dict(id='uncertain-row',revision='a'*64,section='415',row='',seat_as_printed='1X',availability='unknown',physical_row=15,source_bbox=[0,606,911,638],raw_ocr='<script>untrusted screenshot text</script>',reasons=['row_missing','availability_unknown'])
state={'signed_in':False,'published':False,'approved':False};job='c'*32

def api(route):
    path=route.request.url.split('/api/')[1];data={};status=200
    if path=='session':status=200 if state['signed_in'] else 401;data={'csrf':'csrf-test'} if state['signed_in'] else {'error':'Please sign in'}
    elif path=='login':state['signed_in']=True;data={'ok':True}
    elif path=='sources':data=[{'index':121,'name':source['source_file']}]
    elif path=='review/queue':data={'sources':[source],'total_pending':0 if state['published'] else 2}
    elif path=='review/sources/121?page=0':data={'source':source,'page':0,'rows':[] if state['published'] else [record,{**record,'id':'other-row','physical_row':16}]}
    elif path=='review/sources/121/image':route.fulfill(status=200,content_type='image/jpeg',body=(ROOT/'static/sources'/source['source_file']).read_bytes());return
    elif path=='review/approve':
        payload=route.request.post_data_json;assert payload['confirmed'] is True;assert payload['source_index']==121;assert len(payload['changes'])==1
        change=payload['changes'][0];assert change['row']=='O';assert change['seat_as_printed']=='2X';assert change['availability']=='sold';assert change['revision']==record['revision'];assert 'price' not in change
        state['approved']=True;data={'id':job,'status':'processing'};status=202
    elif path==f'review/jobs/{job}':state['published']=True;data={'status':'published','reviewed_count':1}
    else:raise AssertionError(path)
    route.fulfill(status=status,content_type='application/json',body=json.dumps(data))
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':390,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/api/**',api)
    page.goto(sys.argv[1]);page.fill('#password','test-password-only');page.locator('#login-form button').click();expect(page.locator('#workspace')).to_be_visible();page.locator('#show-catalog-review').click()
    expect(page.locator('#queue-rows tr')).to_have_count(2);row=page.locator('#queue-rows tr').first
    row.locator('button').click();expect(page.locator('#queue-evidence svg')).to_be_visible();expect(page.locator('#queue-evidence pre')).to_contain_text('<script>untrusted screenshot text</script>');assert page.locator('#queue-evidence script').count()==0
    row.locator('[data-field="row"]').fill('O');row.locator('[data-field="seat_as_printed"]').fill('2X');row.locator('[data-field="availability"]').select_option('sold')
    expect(row.locator('[data-select]')).to_be_checked();page.locator('#queue-save').click();assert not state['approved'];expect(page.locator('#message')).to_contain_text('Confirm the selected')
    page.check('#queue-confirmed');page.locator('#queue-save').click();expect(page.locator('#message')).to_contain_text('Corrections saved');assert state['approved']
    # Empty pending pages can be navigated/refreshed without null checkbox errors.
    page.locator('#queue-refresh').click();page.select_option('#queue-filter','all');page.locator('#show-upload').click();expect(page.locator('#upload-form')).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
    page.screenshot(path=str(ROOT/'artifacts/admin-review-mobile.png'),full_page=True)
    print('Admin catalog browser passed: source row crop, escaped raw OCR, selective edits, sold status, explicit confirmation, publication, empty queue and mobile layout.');browser.close()
