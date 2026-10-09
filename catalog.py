"""Public catalog; production prompts and unapproved assets are never inputs."""
import html
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
TYPES = {"devotional": "Read", "music": "Listen", "audio": "Listen", "video": "Watch", "download": "Download"}

def safe_url(value):
    parsed = urlparse(value)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError('Public media links must use HTTPS')
    if '[' in value or ']' in value:
        raise ValueError('Unresolved media link')
    return value

def build_catalog(devotions, out, site_url, render_md, fill, templates):
    import build
    entries = list(devotions)
    seen = set()
    for source in sorted((ROOT / 'content' / 'catalog').glob('*.json')):
        data = json.loads(source.read_text())
        for key in ('title', 'slug', 'series', 'type', 'description', 'publish_at', 'status'):
            if not data.get(key): raise ValueError(f'Missing {key} in {source}')
        if data['type'] not in TYPES: raise ValueError('Unknown catalog type')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', data['slug']): raise ValueError('Invalid catalog slug')
        if data['slug'] in seen: raise ValueError('Duplicate catalog slug')
        seen.add(data['slug'])
        if not build.visible(data, data['publish_at']): continue
        url = safe_url(data['external_url'])
        e = dict(data, url=url, teaser=data['description'], card='', subtitle=data['series'])
        entries.append(e)
    entries.sort(key=lambda e: datetime.fromisoformat(e['publish_at']), reverse=True)
    cards=[]
    for e in entries:
        image=f'<img src="{html.escape(e["card"],quote=True)}" alt="" loading="lazy" width="1200" height="630">' if e['card'] else '<div class="format-art" aria-hidden="true">'+html.escape(e['type'].upper())+'</div>'
        display=datetime.fromisoformat(e['publish_at']).astimezone(ZoneInfo('America/Chicago')).strftime('%b %d, %Y · %I:%M %p')
        draft='<span class="draft-label">Draft preview</span>' if e['status']=='draft' else ''
        cards.append(f'<article class="catalog-card" data-type="{e["type"]}" data-series="{html.escape(e["series"],quote=True)}"><a class="catalog-art" href="{html.escape(e["url"],quote=True)}">{image}</a><div class="catalog-copy"><p class="eyebrow">{html.escape(e["series"])} · {e["type"]}</p>{draft}<h3><a href="{html.escape(e["url"],quote=True)}">{html.escape(e["title"])}</a></h3><p>{html.escape(e["teaser"])}</p><div class="catalog-bottom"><time datetime="{html.escape(e["publish_at"],quote=True)}">{display} CT</time><a class="text-link" href="{html.escape(e["url"],quote=True)}">{TYPES[e["type"]]} →</a></div></div></article>')
    formats=''.join(f'<button type="button" data-filter="{kind}" aria-pressed="false">{label}</button>' for kind,label in [('devotional','Devotionals'),('music','Music'),('audio','Audio'),('video','Video'),('download','Downloads')] if any(e['type']==kind for e in entries))
    series=''.join(f'<option value="{html.escape(name,quote=True)}">{html.escape(name)}</option>' for name in sorted({e['series'] for e in entries}))
    latest=devotions[0]
    page=fill((templates/'index.html').read_text(),{'LATEST_URL':latest['url'],'LATEST_TITLE':html.escape(latest['title']),'LATEST_TEASER':html.escape(latest['teaser']),'LATEST_CARD':latest['card'],'CATALOG_CARDS':'\n'.join(cards),'FORMAT_FILTERS':formats,'SERIES_OPTIONS':series,'CATALOG_COUNT':str(len(entries)),'SITE_URL':site_url,'DEVOTION_LIST':''})
    (out/'index.html').write_text(page)
    # Export only the reader-facing metadata, never source blocks or prompts.
    (out/'catalog.json').write_text(json.dumps([{k:e[k] for k in ('title','series','type','url','publish_at','status')} for e in entries],indent=2))
