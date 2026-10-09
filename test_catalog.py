import json
import os
import unittest
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
import build
from catalog import safe_url

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self, tag, attrs):
        for key,value in attrs:
            if key in ('src','href') and value: self.links.append(value)

class CatalogTests(unittest.TestCase):
    def test_draft_and_future_content_stay_unpublished(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(build.visible({'status':'draft','publish_at':'2026-01-01T08:00:00-06:00'},''))
            self.assertFalse(build.visible({'status':'published','publish_at':'2099-01-01T08:00:00-06:00'},''))
            self.assertTrue(build.visible({'status':'published','publish_at':'2026-01-01T08:00:00-06:00'},''))
    def test_twice_daily_order_and_daylight_saving(self):
        morning=build.publication({'publish_at':'2026-10-09T08:00:00-05:00'},'')
        evening=build.publication({'publish_at':'2026-10-09T17:00:00-05:00'},'')
        self.assertGreater(evening,morning)
        self.assertEqual(build.publication({'publish_date':'2026-07-01'},'').utcoffset().total_seconds(),-18000)
        self.assertEqual(build.publication({'publish_date':'2026-12-01'},'').utcoffset().total_seconds(),-21600)
    def test_unsafe_or_unresolved_media_links_rejected(self):
        for value in ['javascript:alert(1)','http://example.com/song','https://example.com/[LINK]','//example.com']:
            with self.assertRaises(ValueError): safe_url(value)
    def test_generated_site_links_and_no_production_prompt_leaks(self):
        self.assertTrue((build.OUT_DIR/'index.html').exists())
        index=(build.OUT_DIR/'index.html').read_text()
        self.assertIn('catalog-search',index)
        self.assertNotIn('Request a pilot seat',index)
        self.assertNotIn('Founding Design Partner',index)
        entries=json.loads((build.OUT_DIR/'catalog.json').read_text())
        self.assertEqual(entries,sorted(entries,key=lambda e:datetime.fromisoformat(e['publish_at']),reverse=True))
        self.assertTrue(all(e['status']=='published' for e in entries))
        self.assertNotIn('philippians-4-9-meaning-do-the-things-youve-seen',json.dumps(entries))
        for page in build.OUT_DIR.rglob('*.html'):
            content=page.read_text(); parser=Links(); parser.feed(content)
            self.assertNotIn('{{',content)
            self.assertNotIn('PRIVATE — DO NOT POST',content)
            self.assertNotIn('NOTEBOOKLM CINEMATIC VIDEO PROMPT',content)
            for link in parser.links:
                if link.startswith(('https:','http:','mailto:','#','data:')): continue
                target=(page.parent/link.split('#')[0]).resolve()
                self.assertTrue(target.is_relative_to(build.OUT_DIR.resolve()),link)
                self.assertTrue(target.exists(),f'{page}: {link}')
