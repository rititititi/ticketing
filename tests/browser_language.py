"""Exercise both interface languages against the app or its static export."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

url=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:5000'
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000},locale='en-US')
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(url)
    expect(page.locator('.ticket-card').first).to_be_visible()
    expect(page.locator('h1')).to_have_text('NCT WISH Gocheok')
    assert 'uu scout' in page.locator('.brand').text_content()
    page.select_option('#review-filter','checked')
    page.select_option('#date','2027-01-15')
    page.select_option('#section-select','F4')
    before=page.locator('.ticket-card').count()
    page.select_option('#language','zh')
    expect(page.locator('html')).to_have_attribute('lang','zh-Hans')
    expect(page.locator('#tickets-title')).to_have_text('区域 F4')
    expect(page.locator('[data-view="sources"]')).to_contain_text('票源图库')
    expect(page.locator('#search')).to_have_attribute('placeholder','搜索区域、排号、座位或备注')
    assert page.locator('.ticket-card').count()==before
    page.locator('.ticket-card').first.click()
    expect(page.locator('#detail-content')).to_contain_text('隐藏部分数字的座位号')
    expect(page.locator('#view-original')).to_have_text('查看原始截图 ↗')
    raw=page.locator('#detail-content pre').inner_text()
    page.locator('#view-original').click()
    expect(page.locator('#source-content')).to_contain_text('本张截图中的全部选项行')
    page.locator('#source-dialog .close').click()
    page.locator('#ticket-dialog .close').click()
    page.select_option('#language','en')
    expect(page.locator('#tickets-title')).to_have_text('Section F4')
    page.locator('.ticket-card').first.click()
    assert page.locator('#detail-content pre').inner_text()==raw
    page.locator('#ticket-dialog .close').click()
    page.select_option('#language','zh')
    page.reload()
    expect(page.locator('.ticket-card').first).to_be_visible()
    expect(page.locator('#language')).to_have_value('zh')
    expect(page.locator('#tickets-title')).to_have_text('全部区域')
    page.locator('[data-view="sources"]').click()
    page.locator('.coverage-panel summary').click()
    expect(page.locator('.coverage-panel summary')).to_contain_text('逐图覆盖情况')
    assert page.locator('#coverage-body tr').count()==79
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.screenshot(path=str(root/'artifacts/uu-scout-zh-mobile.png'))
    page.locator('[data-view="explorer"]').click()
    page.select_option('#review-filter','checked')
    page.select_option('#date','2027-01-15')
    page.select_option('#section-select','F4')
    expect(page.locator('#tickets-title')).to_have_text('区域 F4')
    page.select_option('#language','en')
    expect(page.locator('#tickets-title')).to_have_text('Section F4')
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    assert not errors,errors
    print('Bilingual browser passed: branding, Chinese/English filters, translated details and sources, unchanged raw evidence, saved preference, coverage, mobile overflow, and no JS errors.')
    browser.close()
