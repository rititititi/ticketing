"""Exercise on-site comparisons in the dynamic app or standalone export."""
import sys
from playwright.sync_api import sync_playwright,expect
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1100,'height':900});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(sys.argv[1]);page.wait_for_selector('.ticket-card');before=page.locator('.ticket-card').count()
    page.check('#below-median');expect(page.locator('.ticket-card').first).to_be_visible()
    after=page.locator('.ticket-card').count();assert 0<after<before,(before,after)
    assert page.evaluate('visible.every(t=>priceComparison(t).below)')
    page.locator('.ticket-card').first.click()
    expect(page.locator('.price-comparison')).to_contain_text('comparable median')
    expect(page.locator('.price-comparison')).to_contain_text('Automatic notifications are not enabled.')
    page.select_option('#language','zh');expect(page.locator('.price-comparison h3')).to_have_text('比较相近票源')
    expect(page.locator('.price-comparison')).to_contain_text('目前尚未启用自动通知')
    page.locator('#ticket-dialog .close').click();page.uncheck('#below-median')
    assert page.locator('.ticket-card').count()==before
    page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert not errors,errors
    print(f'Price comparison browser passed: {after} below-median options, detail benchmark, Mandarin, reset and mobile layout.');browser.close()
