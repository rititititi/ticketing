"""Run with the host Python that provides Playwright and system Chromium."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    response=page.goto('http://127.0.0.1:5000')
    assert response.status==200
    page.wait_for_selector('.ticket-card')
    assert page.locator('.section-group').count()==107
    page.locator('path[data-name="F4"]').click()
    assert page.locator('#tickets-title').inner_text()=='Section F4'
    assert page.locator('.ticket-card').count()>0
    page.locator('.ticket-card').first.click()
    assert page.locator('#ticket-dialog').is_visible()
    assert 'Masked seat' in page.locator('#detail-content').inner_text()
    page.locator('#view-original').click()
    assert page.locator('#source-dialog').is_visible()
    page.locator('#source-dialog .close').click()
    page.locator('#ticket-dialog .close').click()
    page.select_option('#date','2027-01-16')
    page.check('#include-sold')
    assert page.locator('.ticket-card.sold').count()==1
    page.select_option('#section-select','T07')
    assert 'No matching records' in page.locator('#tickets').inner_text()
    page.select_option('#date','2026-01-16')
    assert page.locator('.ticket-card').count()==7
    page.locator('#clear-section').click()
    page.select_option('#date','2027-01-15')
    page.uncheck('#include-sold')
    page.locator('path[data-name="F4"]').focus()
    page.keyboard.press('Enter')
    assert page.locator('#tickets-title').inner_text()=='Section F4'
    with page.expect_download() as download:
        page.locator('#download').click()
    assert download.value.suggested_filename.endswith('.csv')
    page.locator('#clear-section').click()
    (ROOT/'artifacts').mkdir(exist_ok=True)
    page.screenshot(path=str(ROOT/'artifacts/desktop.png'),full_page=True)
    page.locator('[data-view="sources"]').click()
    assert page.locator('.source-card').count()==79
    page.fill('#source-search','2781793688755')
    assert page.locator('.source-card').count()==1
    page.locator('.source-card').click()
    assert page.locator('#source-dialog').is_visible()
    page.locator('#source-dialog .close').click()
    page.locator('[data-view="explorer"]').click()
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.select_option('#section-select','F12')
    assert page.locator('.ticket-card').count()>0
    page.locator('.ticket-card').first.click()
    assert page.locator('#ticket-dialog').is_visible()
    page.locator('#ticket-dialog .close').click()
    page.screenshot(path=str(ROOT/'artifacts/mobile.png'),full_page=True)
    assert not errors,errors
    print('Browser passed: section clicks, keyboard selection, dates, sold records, details, source images, source search, CSV download, mobile layout; no JS errors.')
    browser.close()
