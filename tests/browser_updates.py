"""The updates section works without accounts and remembers read state on this browser."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(sys.argv[1]);expect(page.locator('.ticket-card').first).to_be_visible();page.locator('[data-view="updates"]').click()
    expect(page.locator('.update-card').first).to_be_visible();assert page.locator('#explorer-view').is_hidden();assert page.locator('#sources-view').is_hidden()
    assert page.locator('.update-card').count()==12;initial=int(page.locator('#update-count').inner_text());assert initial>12
    page.locator('#updates-more').click();assert page.locator('.update-card').count()==24
    page.select_option('#updates-type','listing_drop');assert page.locator('.update-card').count()>0
    expect(page.locator('.update-card').first).to_contain_text('Price drop in updated listing')
    page.locator('[data-update-before]').first.click();expect(page.locator('#ticket-dialog')).to_be_visible();expect(page.locator('#detail-content')).to_contain_text('supplier quote');page.locator('#ticket-dialog .close').click()
    assert int(page.locator('#update-count').inner_text())==initial-1
    page.select_option('#language','zh');expect(page.locator('#updates-title')).to_have_text('最新动态');expect(page.locator('.update-card').first).to_contain_text('更新票源中的降价')
    page.locator('#updates-read-all').click();expect(page.locator('#update-count')).to_have_text('0');page.check('#updates-unread');expect(page.locator('#updates-list')).to_contain_text('暂无匹配动态')
    page.reload();expect(page.locator('#updates-view')).to_be_visible();assert page.url.endswith('#updates');page.uncheck('#updates-unread');expect(page.locator('.update-card').first).to_be_visible();expect(page.locator('#update-count')).to_have_text('0')
    page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=str(Path(__file__).resolve().parents[1]/'artifacts/updates-mobile.png'),full_page=True)
    assert not errors,errors
    print('Updates browser passed: feed categories, previous/current evidence, pagination, read state persistence, Mandarin and mobile layout.');browser.close()
