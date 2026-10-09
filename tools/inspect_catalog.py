"""Exercise search and phone layouts against the generated review artifact."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

site = Path('_review_site').resolve()
screens = Path('_catalog_screens')
screens.mkdir(exist_ok=True)
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(site)))
Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}'
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(url,wait_until='networkidle')
    page.evaluate('document.fonts.ready')
    assert page.locator('.catalog-card').count()==12
    assert page.evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
    page.screenshot(path=str(screens/'desktop.png'),full_page=True)
    page.locator('#catalog-search').fill('Philippians 4:9')
    assert page.locator('.catalog-card:visible').count()==1
    page.locator('#catalog-search').fill('no-matching-title-12345')
    assert page.locator('#catalog-empty').is_visible()
    page.locator('#catalog-search').fill('')
    page.get_by_role('button',name='Devotionals',exact=True).click()
    assert page.locator('.catalog-card:visible').count()==12
    for width in (390,320):
        page.set_viewport_size({'width':width,'height':844})
        page.goto(url,wait_until='networkidle')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'Homepage overflow at {width}'
        page.screenshot(path=str(screens/f'phone-{width}.png'),full_page=True)
        page.goto(url+'/devotions/philippians-4-9-meaning-do-the-things-youve-seen/',wait_until='networkidle')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'Reader overflow at {width}'
        assert page.get_by_text("Somebody would need one.",exact=False).is_visible()
        page.screenshot(path=str(screens/f'reader-{width}.png'),full_page=True)
    assert not errors,errors
    browser.close()
server.shutdown()
print('Browser checks PASS: desktop, 390px and 320px phones, images, search, empty state, filters, draft reader.')
