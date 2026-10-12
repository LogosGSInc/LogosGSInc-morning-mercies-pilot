"""Fail when generated HTML contains a broken local link or media reference."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        self.links.extend(v for k,v in attrs if k in {'href','src','poster'} and v)

def check(root):
    failures=[]
    for page in root.rglob('*.html'):
        parser=Links(); parser.feed(page.read_text())
        for link in parser.links:
            p=urlsplit(link)
            if p.scheme or p.netloc or not p.path: continue
            target=(root / unquote(p.path).lstrip('/')) if p.path.startswith('/') else (page.parent / unquote(p.path))
            if not target.exists(): failures.append(f'{page.relative_to(root)} -> {link}')
    if failures: raise SystemExit('\n'.join(failures))
    print('All generated local links and asset references resolve.')

if __name__=='__main__': check(Path(__file__).resolve().parents[1]/'_site')
