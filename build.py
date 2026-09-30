from __future__ import annotations
import html, os, re, shutil, textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CONTENT_DIR=ROOT/"content"/"devotions"; TEMPLATE_DIR=ROOT/"templates"; ASSET_DIR=ROOT/"assets"; OUT_DIR=ROOT/"_site"
SITE_URL=os.environ.get("SITE_URL","https://logosgsinc.github.io/LogosGSInc-morning-mercies-pilot/").rstrip("/")+"/"
PILOT_BLOCK='''<p class="eyebrow">Founding Design Partner Pilot</p><h2>Help shape Morning Mercies.</h2><p>Seven Founding Design Partners will read with us for a 14-day pilot and share what strengthens them, what distracts them, and what should change before the first 30-day volume is published. Applications stay open for seven calendar days after the public call begins.</p><ul class="feedback-points"><li>Did the story stay with you?</li><li>Was the Scripture clear and faithful?</li><li>Did the prayer help you carry it into the day?</li><li>How did this page feel to read?</li></ul><p class="pilot-mini">The first three completed 30-day Morning Mercies digital volumes will be provided at no cost. Founding Design Partner recognition is optional and requires your permission.</p><a class="button primary full" href="mailto:morningmercies.pilot@gmail.com?subject=Morning%20Mercies%20Founding%20Design%20Partner">Request a pilot seat</a>'''

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
            while i<len(lines) and lines[i].strip().startswith(">"): qs.append(inline_md(lines[i].strip()[1:].lstrip().rstrip())); i+=1
            out.append("<blockquote><p>"+"<br>\n".join(qs)+"</p></blockquote>"); continue
        if s.startswith("- "):
            items=[]
            while i<len(lines) and lines[i].strip().startswith("- "): items.append(inline_md(lines[i].strip()[2:].strip())); i+=1
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

def wrap_title(text,width=29):
    return textwrap.wrap(text.upper(),width=width)[:3]

def card_svg(meta):
    lines=wrap_title(meta.get("card_title",meta["title"])); sy=330-(len(lines)-1)*30
    nodes="".join(f'<text x="600" y="{sy+i*58}" text-anchor="middle" fill="#f4eedd" font-family="Georgia,serif" font-weight="700" font-size="46">{html.escape(line)}</text>' for i,line in enumerate(lines))
    scripture=html.escape(meta.get("card_scripture",meta.get("root_verse","MORNING MERCIES")).upper())
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"><defs><linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0c1b30"/><stop offset=".58" stop-color="#07111f"/><stop offset="1" stop-color="#030811"/></linearGradient><linearGradient id="m" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#f2eee6"/><stop offset=".2" stop-color="#8f959d"/><stop offset=".4" stop-color="#d7d9dc"/><stop offset=".62" stop-color="#6d737b"/><stop offset=".82" stop-color="#ece9e2"/><stop offset="1" stop-color="#969ca4"/></linearGradient></defs><rect width="1200" height="630" fill="#02060c"/><rect x="18" y="18" width="1164" height="594" rx="34" fill="url(#m)"/><rect x="42" y="42" width="1116" height="546" rx="28" fill="url(#b)" stroke="#c7c9cc" stroke-width="3"/><text x="600" y="126" text-anchor="middle" fill="#e3c791" font-family="cursive" font-style="italic" font-size="56">Morning Mercies</text><text x="600" y="208" text-anchor="middle" fill="#f0ece5" font-family="cursive" font-weight="700" font-size="74">Authored by Grace</text><line x1="330" y1="246" x2="870" y2="246" stroke="#b8bdc5" stroke-width="2"/>{nodes}<text x="600" y="505" text-anchor="middle" fill="#d9c79f" font-family="Georgia,serif" font-style="italic" font-size="27">{scripture}</text><text x="600" y="552" text-anchor="middle" fill="#c4b89f" font-family="Georgia,serif" font-size="18">WITNESS FOR DAILY DEVOTION</text><text x="1060" y="562" text-anchor="end" fill="#c9cdd4" font-family="cursive" font-style="italic" font-size="30">D. W. Smith</text></svg>'''

def cover_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350"><defs><linearGradient id="b" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#0c1b30"/><stop offset=".55" stop-color="#07111f"/><stop offset="1" stop-color="#030811"/></linearGradient><linearGradient id="m" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#f2eee6"/><stop offset=".2" stop-color="#8f959d"/><stop offset=".4" stop-color="#d7d9dc"/><stop offset=".62" stop-color="#6d737b"/><stop offset=".82" stop-color="#ece9e2"/><stop offset="1" stop-color="#969ca4"/></linearGradient></defs><rect width="1080" height="1350" fill="#02060c"/><rect x="28" y="26" width="1024" height="1298" rx="54" fill="url(#m)"/><rect x="62" y="60" width="956" height="1230" rx="42" fill="#17191d"/><rect x="78" y="76" width="924" height="1198" rx="34" fill="url(#b)" stroke="#c7c9cc" stroke-width="4"/><text x="540" y="270" text-anchor="middle" fill="#e3c791" font-family="cursive" font-style="italic" font-size="88">Morning Mercies</text><text x="540" y="500" text-anchor="middle" fill="#f1ede6" font-family="cursive" font-weight="700" font-size="122">Authored by Grace</text><text x="540" y="615" text-anchor="middle" fill="#e3c791" font-family="cursive" font-style="italic" font-size="60">Witness for daily devotion</text><text x="540" y="715" text-anchor="middle" fill="#c9cdd4" font-family="Georgia,serif" font-size="27">AN AUTHORED BY GRACE PUBLICATION</text><text x="540" y="1210" text-anchor="middle" fill="#d9c79f" font-family="cursive" font-style="italic" font-size="62">D. W. Smith</text></svg>'''

def build():
    if OUT_DIR.exists(): shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True); shutil.copytree(ASSET_DIR,OUT_DIR/"assets"); (OUT_DIR/".nojekyll").write_text("")
    (OUT_DIR/"assets"/"cover.svg").write_text(cover_svg(),encoding="utf-8")
    dt=(TEMPLATE_DIR/"devotion.html").read_text(); it=(TEMPLATE_DIR/"index.html").read_text()
    (OUT_DIR/"assets"/"og").mkdir(parents=True,exist_ok=True); (OUT_DIR/"share").mkdir(parents=True,exist_ok=True)
    entries=[]; seen=set()
    for source in sorted(CONTENT_DIR.glob("*.md")):
        meta,body=parse_front_matter(source.read_text()); slug=meta["slug"]
        if slug in seen: raise ValueError("Duplicate slug"); seen.add(slug)
        short,long=split_forms(body); long=strip_duplicate_intro(long,meta["title"]); taste=teaser(meta,short)
        page_url=SITE_URL+f"devotions/{slug}/"; card_rel=f"assets/og/{slug}.png"; card_url=SITE_URL+card_rel
        (OUT_DIR/"assets"/"og"/f"{slug}.svg").write_text(card_svg(meta))
        page=OUT_DIR/"devotions"/slug; page.mkdir(parents=True,exist_ok=True)
        (page/"index.html").write_text(fill(dt,{"TITLE":html.escape(meta["title"]),"DESCRIPTION":html.escape(meta["description"],quote=True),"PAGE_URL":page_url,"SHARE_IMAGE_URL":card_url,"SHARE_IMAGE_REL":f"../../{card_rel}","ASSET_PREFIX":"../../","ROOT_VERSE":html.escape(meta.get("root_verse","Scripture")),"TRANSLATION":html.escape(meta.get("translation","KJV")),"BODY_HTML":markdown_to_html(long),"AUTHOR":html.escape(meta["author"]),"PILOT_BLOCK":PILOT_BLOCK}))
        (OUT_DIR/"share"/f"{slug}.txt").write_text(f"{taste}\n\nRead today’s Morning Mercy:\n{page_url}\n\n#MorningMercies #AuthoredByGrace #DailyDevotion #BibleDevotional\n")
        entries.append({"title":meta["title"],"subtitle":f"{meta.get('root_verse','')} · {meta.get('translation','KJV')}","url":f"devotions/{slug}/","day":meta.get("day",""),"teaser":taste,"card":card_rel})
    entries.sort(key=lambda e:int(e.get("day") or 0),reverse=True); latest=entries[0]
    items=[]
    for e in entries:
        items.append(f'<li><a href="{e["url"]}"><span class="devotion-number">DAY {html.escape(e["day"] or "—")}</span><span><span class="item-title">{html.escape(e["title"])}</span><span class="item-meta">{html.escape(e["subtitle"])}</span></span><span class="item-arrow">→</span></a></li>')
    (OUT_DIR/"index.html").write_text(fill(it,{"LATEST_URL":latest["url"],"LATEST_TITLE":html.escape(latest["title"]),"LATEST_TEASER":html.escape(latest["teaser"]),"LATEST_CARD":latest["card"],"DEVOTION_LIST":"\n".join(items)}))
    print(f"Built {len(entries)} devotion(s)")

if __name__=="__main__": build()
