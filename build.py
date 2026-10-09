from __future__ import annotations
import html, os, re, shutil, json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from datetime import date
import cards
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CONTENT_DIR=ROOT/"content"/"devotions"; TEMPLATE_DIR=ROOT/"templates"; ASSET_DIR=ROOT/"assets"; OUT_DIR=ROOT/"_site"
SITE_URL=os.environ.get("SITE_URL","https://logosgsinc.github.io/LogosGSInc-morning-mercies-pilot/").rstrip("/")+"/"
PILOT_BLOCK='<p class="eyebrow">Authored by Grace</p><h2>Carry the Word into your day.</h2><p>Scripture, story, and prayer. Read the daily devotionals and explore the growing collection.</p><a class="button primary full" href="../../index.html#catalog">Browse the catalog</a>'

def publication(meta, fallback):
    value=meta.get("publish_at", meta.get("publish_date", fallback))
    moment=datetime.fromisoformat(value)
    if moment.tzinfo is None:
        moment=moment.replace(tzinfo=ZoneInfo("America/Chicago"))
    return moment

def visible(meta, fallback):
    status=meta.get("status", "published")
    if status not in {"draft", "published"}: raise ValueError("Invalid publication status")
    if os.environ.get("INCLUDE_DRAFTS")=="1": return True
    return status=="published" and publication(meta, fallback)<=datetime.now(timezone.utc)


def parse_front_matter(text):
    if not text.startswith("---\n"): raise ValueError("Devotion file must start with front matter")
    end=text.find("\n---\n",4)
    if end<0: raise ValueError("Front matter missing closing ---")
    meta={}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"): continue
        if ":" not in line: raise ValueError(f"Invalid front matter: {line}")
        k,v=line.split(":",1); v=v.strip()
        if len(v)>=2 and v[0]==v[-1] and v[0] in {'"',"'"}: v=v[1:-1]
        meta[k.strip()]=v
    for k in ("title","slug","description","author"):
        if not meta.get(k): raise ValueError(f"Missing {k}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",meta["slug"]): raise ValueError("Invalid slug")
    return meta,text[end+5:].lstrip()

def split_forms(body):
    a=body.find("# Morning Mercy"); b=body.find("# Morning Mercies Book Devotional")
    return (body[a+len("# Morning Mercy"):b].strip(),body[b+len("# Morning Mercies Book Devotional"):].strip()) if a>=0 and b>a else (body.strip(),body.strip())

def strip_duplicate_intro(md,title):
    lines=md.splitlines(); out=[]; st=ss=False
    for line in lines:
        s=line.strip()
        if not st and s.startswith("## ") and s[3:].strip().casefold()==title.casefold(): st=True; continue
        if st and not ss and s.startswith("### "): ss=True; continue
        out.append(line)
    return "\n".join(out).strip()

def inline_md(text):
    safe=html.escape(text,quote=False)
    safe=re.sub(r"\*\*(.+?)\*\*",r"<strong>\1</strong>",safe)
    return re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)",r"<em>\1</em>",safe)

def markdown_to_html(source):
    lines=source.splitlines(); out=[]; i=0
    while i<len(lines):
        s=lines[i].strip()
        if not s: i+=1; continue
        if s=="---": out.append("<hr>"); i+=1; continue
        level=next((n for n in (4,3,2,1) if s.startswith("#"*n+" ")),None)
        if level: out.append(f"<h{min(level,4)}>{inline_md(s[level+1:].strip())}</h{min(level,4)}>"); i+=1; continue
        if s.startswith(">"):
            qs=[]
            while i<len(lines) and lines[i].strip().startswith(">"):
                qs.append(inline_md(lines[i].strip()[1:].lstrip().rstrip())); i+=1
            out.append("<blockquote><p>"+"<br>\n".join(qs)+"</p></blockquote>"); continue
        if s.startswith("- "):
            items=[]
            while i<len(lines) and lines[i].strip().startswith("- "):
                items.append(inline_md(lines[i].strip()[2:].strip())); i+=1
            out.append("<ul>"+"".join(f"<li>{x}</li>" for x in items)+"</ul>"); continue
        p=[]
        while i<len(lines):
            cur=lines[i].strip()
            if not cur or cur=="---" or cur.startswith("#") or cur.startswith(">") or cur.startswith("- "): break
            p.append(cur); i+=1
        if p: out.append("<p>"+inline_md(" ".join(p))+"</p>"); continue
        i+=1
    return "\n".join(out)

def fill(t,r):
    for k,v in r.items(): t=t.replace("{{"+k+"}}",v)
    left=re.findall(r"\{\{([A-Z0-9_]+)\}\}",t)
    if left: raise ValueError("Unresolved: "+",".join(sorted(set(left))))
    return t

def plain_text(md):
    md=re.sub(r"^#+\s+.*$","",md,flags=re.M); md=re.sub(r"^>\s?","",md,flags=re.M); md=re.sub(r"^[-*]\s+","",md,flags=re.M)
    return re.sub(r"\s+"," ",md.replace("**","").replace("*","")).strip()

def teaser(meta,short):
    if meta.get("social_teaser"): return meta["social_teaser"]
    t=plain_text(short.split("### Prayer",1)[0])
    return t if len(t)<=330 else t[:330].rsplit(" ",1)[0]+"…"

def cover_svg():
    # The site cover now uses the same 1200x630 landscape geometry and the
    # same approved house artwork as the daily cards. This keeps the series
    # identity stable while daily copy changes independently.
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-labelledby="title desc">
<title id="title">Morning Mercies — Authored by Grace</title>
<desc id="desc">Morning Mercies landscape series cover with the established navy and warm-gold devotional artwork.</desc>
<defs>
  <linearGradient id="shade" x1="0" x2="1"><stop offset="0" stop-color="#02070c" stop-opacity=".94"/><stop offset=".58" stop-color="#02070c" stop-opacity=".62"/><stop offset="1" stop-color="#02070c" stop-opacity=".08"/></linearGradient>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity=".75"/></filter>
</defs>
<image href="cards/house-background.png" x="0" y="0" width="1200" height="630" preserveAspectRatio="xMidYMid slice"/>
<rect x="0" y="0" width="1200" height="630" fill="url(#shade)"/>
<g fill="#ffe6bd" text-anchor="middle" filter="url(#shadow)">
  <text x="455" y="130" font-family="'Great Vibes','Brush Script MT',cursive" font-size="82">Morning Mercies</text>
  <line x1="190" y1="157" x2="720" y2="157" stroke="#d9ad67" stroke-width="2" opacity=".9"/>
  <text x="455" y="280" font-family="'Great Vibes','Brush Script MT',cursive" font-size="92">Authored by Grace</text>
  <text x="455" y="342" font-family="'Cormorant Garamond',Georgia,serif" font-size="32" font-style="italic">Witness for daily devotion</text>
  <line x1="260" y1="378" x2="650" y2="378" stroke="#d9ad67" stroke-width="2" opacity=".85"/>
  <text x="455" y="430" font-family="'Cormorant Garamond',Georgia,serif" font-size="24" letter-spacing="4">AN AUTHORED BY GRACE PUBLICATION</text>
  <text x="455" y="492" font-family="'Cormorant Garamond',Georgia,serif" font-size="27" letter-spacing="5">SCRIPTURE · STORY · PRAYER</text>
</g>
<text x="1030" y="555" fill="#ffe6bd" text-anchor="middle" font-family="'Great Vibes','Brush Script MT',cursive" font-size="52" filter="url(#shadow)">D. W. Smith</text>
</svg>'''

def build():
    if OUT_DIR.exists(): shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True); shutil.copytree(ASSET_DIR,OUT_DIR/"assets"); (OUT_DIR/".nojekyll").write_text("")
    (OUT_DIR/"assets"/"cover.svg").write_text(cover_svg(),encoding="utf-8")
    dt=(TEMPLATE_DIR/"devotion.html").read_text(); it=(TEMPLATE_DIR/"index.html").read_text()
    (OUT_DIR/"assets"/"og").mkdir(parents=True,exist_ok=True); (OUT_DIR/"share").mkdir(parents=True,exist_ok=True)
    entries=[]; seen=set()
    for source in sorted(CONTENT_DIR.glob("*.md")):
        meta,body=parse_front_matter(source.read_text()); slug=meta["slug"]
        if not visible(meta, source.name[:10]): continue
        if slug in seen: raise ValueError("Duplicate slug")
        seen.add(slug)
        short,long=split_forms(body); long=strip_duplicate_intro(long,meta["title"]); taste=teaser(meta,short)
        page_url=SITE_URL+f"devotions/{slug}/"; card_rel=f"assets/og/{slug}.png"; card_url=SITE_URL+card_rel
        cards.render(cards.metadata(meta, short)).save(OUT_DIR/"assets"/"og"/f"{slug}.png")
        page=OUT_DIR/"devotions"/slug; page.mkdir(parents=True,exist_ok=True)
        (page/"index.html").write_text(fill(dt,{"TITLE":html.escape(meta["title"]),"DESCRIPTION":html.escape(meta["description"],quote=True),"PAGE_URL":page_url,"SHARE_IMAGE_URL":card_url,"SHARE_IMAGE_REL":f"../../{card_rel}","ASSET_PREFIX":"../../","ROOT_VERSE":html.escape(meta.get("root_verse","Scripture")),"TRANSLATION":html.escape(meta.get("translation","KJV")),"BODY_HTML":markdown_to_html(long),"AUTHOR":html.escape(meta["author"]),"PILOT_BLOCK":PILOT_BLOCK}))
        (OUT_DIR/"share"/f"{slug}.txt").write_text(f"{taste}\n\nRead today’s Morning Mercy:\n{page_url}\n\n#MorningMercies #AuthoredByGrace #DailyDevotion #BibleDevotional\n")
        entries.append({"title":meta["title"],"subtitle":f"{meta.get('root_verse','')} · {meta.get('translation','KJV')}","url":f"devotions/{slug}/","day":meta.get("day",""),"teaser":taste,"card":card_rel,"publish_date":meta.get("publish_date",source.name[:10]),"publish_at":publication(meta,source.name[:10]).isoformat(),"series":meta.get("series","Morning Mercies"),"type":"devotional","status":meta.get("status","published")})
    for entry in entries:
        date.fromisoformat(entry["publish_date"])
    entries.sort(key=lambda e:datetime.fromisoformat(e["publish_at"]),reverse=True)
    if not entries: raise ValueError("No devotion content")
    latest=entries[0]
    items=[]
    for e in entries:
        items.append(f'<li><a href="{e["url"]}"><span class="devotion-number">DAY {html.escape(e["day"] or "—")}</span><span><span class="item-title">{html.escape(e["title"])}</span><span class="item-meta">{html.escape(e["subtitle"])}</span></span><span class="item-arrow">→</span></a></li>')
    (OUT_DIR/"index.html").write_text(fill(it,{"LATEST_URL":latest["url"],"LATEST_TITLE":html.escape(latest["title"]),"LATEST_TEASER":html.escape(latest["teaser"]),"LATEST_CARD":latest["card"],"DEVOTION_LIST":"\n".join(items)}))
    from catalog import build_catalog
    build_catalog(entries, OUT_DIR, SITE_URL, markdown_to_html, fill, TEMPLATE_DIR)
    print(f"Built {len(entries)} devotion(s)")

if __name__=="__main__": build()

