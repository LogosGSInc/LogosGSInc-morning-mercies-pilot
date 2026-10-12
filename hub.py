"""Static Authored by Grace catalog; uses the existing devotional builder/artwork."""
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

SERIES = {"Morning Mercies": "morning-mercies", "On Watch": "on-watch"}
KINDS = {"song": "Song", "podcast": "Podcast", "video": "Deep dive", "promo": "Preview"}

def esc(value):
    return html.escape(str(value), quote=True)

def https_url(value):
    p = urlparse(value)
    if p.scheme != "https" or not p.netloc or p.username or p.password:
        raise ValueError("Public media/link URLs must use HTTPS without credentials")
    return value

def ready(record, now=None):
    if record.get("status") != "approved":
        return False
    stamp = datetime.fromisoformat(record["publish_at"].replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("publish_at requires a timezone offset")
    return stamp <= (now or datetime.now(timezone.utc))

def validate_media(record):
    for field in ("id", "title", "description", "series", "type", "publish_at", "transcript"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError(f"Missing media field: {field}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", record["id"]):
        raise ValueError("Invalid media ID")
    if record["series"] not in SERIES or record["type"] not in KINDS:
        raise ValueError("Unknown media type or series")
    if record.get("status") not in {"draft", "approved"}:
        raise ValueError("Unknown publication status")
    stamp = datetime.fromisoformat(record["publish_at"].replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("publish_at requires a timezone offset")
    if not record.get("audio_url") and not record.get("video_url"):
        raise ValueError("Media requires audio_url or video_url")
    if record["type"] in {"song", "podcast"} and not record.get("audio_url"):
        raise ValueError("Songs and podcasts require audio")
    if record["type"] == "video" and not record.get("video_url"):
        raise ValueError("Deep dives require video")
    for key in ("audio_url", "video_url", "poster_url", "captions_url"):
        if record.get(key):
            https_url(record[key])
    if record.get("video_url") and not record.get("captions_url"):
        raise ValueError("Video requires reviewed WebVTT captions")
    if record.get("status") == "approved":
        if record.get("editorial_approved") is not True:
            raise ValueError("Editorial approval is required")
        for medium in ("audio", "video"):
            if record.get(medium + "_url") and record.get(medium + "_qc_passed") is not True:
                raise ValueError(f"Rendered {medium} QC is required")
    path = record.get("article_path", "")
    if path and not re.fullmatch(r"(?:devotions|articles)/[a-z0-9-]+/", path):
        raise ValueError("article_path must be a canonical internal article path")
    return record

def navigation(prefix=""):
    links = [("Read", "read/"), ("Listen", "listen/"), ("Watch", "watch/")]
    main = "".join(f'<a href="{prefix}{path}">{label}</a>' for label, path in links)
    return f'''<a class="skip-link" href="#main">Skip to content</a><nav class="abg-nav" aria-label="Main navigation">
<a class="nav-brand" href="{prefix}">Authored by Grace</a><div class="nav-links">{main}
<details class="nav-menu"><summary>Explore</summary><div class="nav-dropdown">
<a href="{prefix}series/morning-mercies/">Morning Mercies</a><a href="{prefix}series/on-watch/">On Watch</a>
<a href="{prefix}previews/">Previews</a><a href="{prefix}about/">About</a><a href="{prefix}contact/">Contact</a>
</div></details></div></nav>'''

def footer(prefix, config):
    extra = f'<a href="{esc(config["substack_url"])}">Subscribe on Substack</a>' if config.get("substack_url") else ""
    socials = ' · '.join(f'<a href="{esc(https_url(url))}">{esc(label)}</a>' for label,url in config.get('social_links',{}).items() if url)
    return f'''<footer class="site-footer"><p class="footer-script">Authored by Grace</p>
<p>Scripture. Story. Prayer.</p><p>{extra} <a href="{prefix}contact/">Contact</a> · <a href="{prefix}privacy/">Privacy</a></p>
<p>{socials}</p><p>An Authored by Grace Publication · D. W. Smith</p></footer>'''

def document(title, description, body, path, build, config):
    prefix = "../" * len(Path(path).parts) if path else ""
    url = build.SITE_URL + path
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — Authored by Grace</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(url)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}">
<meta property="og:image" content="{esc(build.SITE_URL)}assets/cards/series-cover-v3.jpg"><meta property="og:url" content="{esc(url)}">
<link rel="stylesheet" href="{prefix}assets/css/morning-mercies.css"><link rel="stylesheet" href="{prefix}assets/css/hub.css">
</head><body>{navigation(prefix)}<main id="main" class="home-shell">{body}</main>{footer(prefix, config)}
<script src="{prefix}assets/js/catalog.js" defer></script></body></html>'''

def player(record):
    out = []
    if record.get("video_url"):
        poster = f' poster="{esc(record["poster_url"])}"' if record.get("poster_url") else ""
        out.append(f'<video controls playsinline crossorigin="anonymous" preload="none"{poster} aria-label="{esc(record["title"])}">'
                   f'<source src="{esc(record["video_url"])}" type="video/mp4">'
                   f'<track kind="captions" src="{esc(record["captions_url"])}" srclang="en" label="English" default>'
                   f'<a href="{esc(record["video_url"])}">Open video</a></video>')
    if record.get("audio_url"):
        out.append(f'<audio controls preload="none" aria-label="{esc(record["title"])}"><source src="{esc(record["audio_url"])}" type="audio/mpeg">'
                   f'<a href="{esc(record["audio_url"])}">Open audio</a></audio>')
    return "\n".join(out)

def card(entry, prefix=""):
    image = f'<img src="{prefix}{esc(entry["image"])}" alt="" loading="lazy">' if entry.get("image") else ""
    text = f'{entry["title"]} {entry["description"]} {entry["series"]} {entry["kind"]}'
    return f'''<article class="catalog-card" data-search="{esc(text.lower())}">{image}<div class="card-copy">
<p class="eyebrow">{esc(entry["series"])} · {esc(entry["kind"])}</p><h2><a href="{prefix}{esc(entry["path"])}">{esc(entry["title"])}</a></h2>
<p>{esc(entry["description"])}</p><p class="item-meta">{esc(entry["date"])}</p></div></article>'''

def catalog(title, intro, entries, prefix):
    cards = "".join(card(e, prefix) for e in entries)
    empty = '<p class="empty-state">New releases will appear here when they are ready.</p>' if not entries else ""
    return f'''<p class="eyebrow">The Authored by Grace catalog</p><h1 class="hub-title">{esc(title)}</h1><p class="hub-lede">{esc(intro)}</p>
<label class="search-label">Find a release<input type="search" data-catalog-search placeholder="Title, Scripture, series…"></label>
<p class="search-status" aria-live="polite" data-search-status></p><div class="catalog-grid">{cards}</div>{empty}'''

def build_hub(build):
    root, out = build.ROOT, build.OUT_DIR
    config = json.loads((root / "site-config.json").read_text())
    if config.get("substack_url"):
        https_url(config["substack_url"])
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", config["contact_email"]):
        raise ValueError("Invalid contact email")
    entries = []
    for src in build.CONTENT_DIR.glob("*.md"):
        meta, _ = build.parse_front_matter(src.read_text())
        entries.append(dict(title=meta["title"], description=meta["description"], series="Morning Mercies", kind="Article",
                            date=meta.get("publish_date", src.name[:10]), path=f'devotions/{meta["slug"]}/', image=f'assets/og/{meta["slug"]}.png'))
    def write(path, title, description, body):
        dest = out / path / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(document(title, description, body, path, build, config))
    for src in (root / "content/articles").glob("*.json"):
        r = json.loads(src.read_text())
        if not ready(r):
            continue
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", r["id"]) or r["series"] not in SERIES:
            raise ValueError("Invalid article ID or series")
        if r.get("editorial_approved") is not True:
            raise ValueError("Article needs editorial approval")
        path = f'articles/{r["id"]}/'
        write(path, r["title"], r["description"], f'<article class="paper"><div class="devotion-head"><p class="eyebrow">{esc(r["series"])}</p><h1>{esc(r["title"])}</h1></div><div class="story-copy">{build.markdown_to_html(r["body"])}</div></article>')
        entries.append(dict(title=r["title"],description=r["description"],series=r["series"],kind="Article",date=r["publish_at"][:10],path=path))
    media = []
    for src in (root / "content/media").glob("*.json"):
        r = validate_media(json.loads(src.read_text()))
        if ready(r):
            media.append(r)
    media.sort(key=lambda r: datetime.fromisoformat(r["publish_at"].replace("Z", "+00:00")), reverse=True)
    for r in media:
        path = f'media/{r["id"]}/'
        related = ""
        if r.get("article_path"):
            if not (out / r["article_path"] / "index.html").exists():
                raise ValueError("Related canonical article is not published")
            related = f'<p><a class="text-link" href="../../{esc(r["article_path"])}">Read the companion article →</a></p>'
        body = f'''<p class="eyebrow">{esc(r["series"])} · {esc(KINDS[r["type"]])}</p><h1 class="hub-title">{esc(r["title"])}</h1>
<p class="hub-lede">{esc(r["description"])}</p><div class="media-player">{player(r)}</div>{related}
<section class="transcript"><h2>{'Lyrics' if r['type']=='song' else 'Transcript'}</h2>{build.markdown_to_html(r["transcript"])}</section>'''
        write(path, r["title"], r["description"], body)
        entries.append(dict(title=r["title"],description=r["description"],series=r["series"],kind=KINDS[r["type"]],date=r["publish_at"][:10],path=path))
        if r.get("article_path"):
            target = out / r["article_path"] / "index.html"
            text = target.read_text()
            section = f'<section class="companion-media"><h2>{esc(r["title"])}</h2>{player(r)}<p><a href="../../{path}">Lyrics / transcript →</a></p></section>'
            target.write_text(text.replace("</main>", section + "</main>"))
    entries.sort(key=lambda e:e["date"], reverse=True)
    for path, title, intro, selected in (
        ("read/", "Read", "Scripture, story, prayer—and a faithful next step.", [e for e in entries if e["kind"] == "Article"]),
        ("listen/", "Listen", "Songs and spoken reflections to carry into your day.", [e for e in entries if e["kind"] in {"Song", "Podcast"}]),
        ("watch/", "Watch", "Short deep dives rooted in Scripture. Watch, reflect, and respond.", [e for e in entries if e["kind"] == "Deep dive"]),
        ("previews/", "Previews", "A first look at stories, songs, and new releases.", [e for e in entries if e["kind"] == "Preview"]),
    ):
        write(path, title, intro, catalog(title,intro,selected,"../"))
    for name, slug in SERIES.items():
        write(f"series/{slug}/", name, f"Explore {name}.", catalog(name, "Read, listen, and watch the releases in this series.", [e for e in entries if e["series"] == name], "../../"))
    email = esc(config["contact_email"])
    write("contact/", "Contact", "Contact Authored by Grace.", f'<h1 class="hub-title">Let’s talk.</h1><p class="hub-lede">Questions, reader feedback, or an invitation to collaborate?</p><p><a class="button primary" href="mailto:{email}">Email Authored by Grace</a></p><p>{email}</p>')
    write("about/", "About", "Scripture. Story. Prayer. Authored by Grace.", '<h1 class="hub-title">Authored by Grace</h1><p class="hub-lede">Scripture. Story. Prayer.</p><div class="transcript"><p>An Authored by Grace Publication · D. W. Smith</p><p>Morning Mercies follows a passage through a story rooted in Scripture and closes in prayer. On Watch brings Scripture, prayer, and a direct call to faithful action.</p><p>Abiding in Christ shapes how we live: pray, repent, and follow Him in the next faithful step.</p></div>')
    write("privacy/", "Privacy", "How this website handles visits and contact.", '<h1 class="hub-title">Privacy</h1><div class="transcript"><p>This site does not ask you to create an account or store an email list. GitHub Pages and the providers serving media may process technical request information, such as IP addresses, to deliver and secure their services.</p><p>The contact button opens your email application. Messages are handled through Proton Mail. External subscriptions and social links use those services’ own privacy practices.</p></div>')
    latest = next(e for e in entries if e["kind"] == "Article")
    featured = next((r for r in media if r["id"] == config.get("featured_media_id")), None)
    if config.get("featured_media_id") and not featured:
        raise ValueError("Pinned featured media must be approved and published")
    featured = featured or next((r for r in media if r["type"] == "video"), None)
    spotlight = (f'<div class="feature-panel"><div><p class="eyebrow">Featured deep dive</p><h2>{esc(featured["title"])}</h2><p>{esc(featured["description"])}</p><a class="text-link" href="media/{esc(featured["id"])}/">Watch with transcript →</a></div><div>{player(featured)}</div></div>' if featured else
                 f'<div class="feature-panel"><div><p class="eyebrow">The latest reading</p><h2>{esc(latest["title"])}</h2><p>{esc(latest["description"])}</p><a class="text-link" href="{latest["path"]}">Continue reading →</a></div><a href="{latest["path"]}"><img src="{latest.get("image", "assets/cards/series-cover-v3.jpg")}" alt="Latest Authored by Grace reading"></a></div>')
    home = f'''<section class="hero"><div class="hero-art-wrap"><img class="hero-art" src="assets/cards/series-cover-v3.jpg" alt="Approved Morning Mercies — Authored by Grace cover"></div>
<div class="hero-copy"><p class="eyebrow">Scripture. Story. Prayer.</p><h1>Begin your morning with mercy made new and the Word.</h1><p class="hero-lede">Stories rooted in Scripture. Songs to carry with you. Prayer that leads to a faithful next step.</p>
<div class="hero-actions"><a class="button primary" href="{latest["path"]}">Read today’s devotional.</a><a class="button ghost" href="listen/">Listen</a><a class="button ghost" href="watch/">Watch</a></div><p class="hero-micro">KJV Scripture quotations · story · prayer</p></div></section>
<section class="spotlight">{spotlight}</section><section class="series-grid"><a href="series/morning-mercies/"><p class="eyebrow">Morning Mercies</p><h2>Begin with the Word.</h2><p>A passage, a story rooted in Scripture, and a closing prayer.</p></a><a href="series/on-watch/"><p class="eyebrow">On Watch</p><h2>Stand your watch.</h2><p>Scripture, prayer, and field orders for the next faithful step.</p></a></section>
<section class="latest-section"><p class="eyebrow">From the catalog</p><h2 class="hub-title">Carry it into your day.</h2><div class="catalog-grid">{''.join(card(e) for e in entries[:6])}</div><p><a class="text-link" href="read/">Explore all readings →</a></p></section>'''
    write("", "Authored by Grace", "Scripture. Story. Prayer. Read Morning Mercies and On Watch; explore songs, podcasts, and short deep dives.", home)
    # Existing devotional URLs and approved artwork remain unchanged.
    for target in (out / "devotions").glob("*/index.html"):
        text = target.read_text().replace('<body>', '<body>' + navigation('../../'))
        text = text.replace('<main class="reader-shell">', '<main id="main" class="reader-shell">')
        text = text.replace('</head>', '<link rel="stylesheet" href="../../assets/css/hub.css"></head>')
        text = text.replace(build.PILOT_BLOCK, '<p class="eyebrow">Authored by Grace</p><h2>Keep reading.</h2><p>Explore Scripture, stories, songs, and prayer.</p><a class="button primary full" href="../../read/">Browse the catalog</a>')
        text = text.replace('</body>', '</body>')
        target.write_text(text)
    (out / "catalog.json").write_text(json.dumps(entries, ensure_ascii=False))
    from xml.sax.saxutils import escape
    urls = [''] + [e['path'] for e in entries] + ['read/','listen/','watch/','contact/','about/']
    (out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{escape(build.SITE_URL+p)}</loc></url>' for p in urls) + '</urlset>')
    (out / "robots.txt").write_text('User-agent: *\nAllow: /\nSitemap: ' + build.SITE_URL + 'sitemap.xml\n')
    print(f"Built Authored by Grace hub: {len(entries)} catalog entries, {len(media)} media releases")
