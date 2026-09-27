from __future__ import annotations

import html
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT_DIR = ROOT / "content" / "devotions"
TEMPLATE_DIR = ROOT / "templates"
ASSET_DIR = ROOT / "assets"
OUT_DIR = ROOT / "_site"

DEFAULT_SITE_URL = "https://logosgsinc.github.io/LogosGSInc-morning-mercies-pilot/"
SITE_URL = os.environ.get("SITE_URL", DEFAULT_SITE_URL).rstrip("/") + "/"


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("Devotion file must start with front matter delimited by ---")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("Front matter is missing its closing ---")
    raw_meta = text[4:end]
    body = text[end + 5 :].lstrip()
    meta: dict[str, str] = {}
    for line in raw_meta.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"Invalid front matter line: {line}")
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        meta[key.strip()] = value
    required = ["title", "slug", "description", "share_image", "author"]
    missing = [key for key in required if not meta.get(key)]
    if missing:
        raise ValueError(f"Missing required front matter: {', '.join(missing)}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", meta["slug"]):
        raise ValueError(f"Slug must be lowercase kebab-case: {meta['slug']}")
    return meta, body


def inline_md(text: str) -> str:
    safe = html.escape(text, quote=False)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", safe)
    return safe


def markdown_to_html(source: str) -> str:
    lines = source.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if stripped == "---":
            out.append("<hr>")
            i += 1
            continue
        if stripped.startswith("### "):
            out.append(f"<h3>{inline_md(stripped[4:].strip())}</h3>")
            i += 1
            continue
        if stripped.startswith("## "):
            out.append(f"<h2>{inline_md(stripped[3:].strip())}</h2>")
            i += 1
            continue
        if stripped.startswith(">"):
            qlines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q = lines[i].strip()[1:].lstrip()
                if q.endswith("  "):
                    q = q[:-2]
                qlines.append(inline_md(q))
                i += 1
            out.append("<blockquote><p>" + "<br>\n".join(qlines) + "</p></blockquote>")
            continue
        if stripped.startswith("- "):
            items: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(inline_md(lines[i].strip()[2:].strip()))
                i += 1
            out.append("<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>")
            continue
        paragraph: list[str] = []
        while i < len(lines):
            current = lines[i].strip()
            if not current:
                break
            if current == "---" or current.startswith("## ") or current.startswith("### ") or current.startswith(">") or current.startswith("- "):
                break
            paragraph.append(current)
            i += 1
        if paragraph:
            out.append("<p>" + inline_md(" ".join(paragraph)) + "</p>")
            continue
        i += 1
    return "\n".join(out)


def fill(template: str, replacements: dict[str, str]) -> str:
    result = template
    for key, value in replacements.items():
        result = result.replace("{{" + key + "}}", value)
    leftovers = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", result)))
    if leftovers:
        raise ValueError(f"Unresolved template placeholders: {', '.join(leftovers)}")
    return result


def absolute_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return SITE_URL + path.lstrip("/")


def build() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    shutil.copytree(ASSET_DIR, OUT_DIR / "assets")
    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    devotion_template = (TEMPLATE_DIR / "devotion.html").read_text(encoding="utf-8")
    index_template = (TEMPLATE_DIR / "index.html").read_text(encoding="utf-8")

    entries: list[dict[str, str]] = []
    seen_slugs: set[str] = set()

    for source in sorted(CONTENT_DIR.glob("*.md")):
        meta, body_md = parse_front_matter(source.read_text(encoding="utf-8"))
        slug = meta["slug"]
        if slug in seen_slugs:
            raise ValueError(f"Duplicate slug: {slug}")
        seen_slugs.add(slug)

        page_dir = OUT_DIR / "devotions" / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        page_url = SITE_URL + f"devotions/{slug}/"

        rendered = fill(devotion_template, {
            "TITLE": html.escape(meta["title"]),
            "KICKER": html.escape(meta.get("kicker", meta.get("scripture", "Morning Mercies"))),
            "SUBTITLE": html.escape(meta.get("subtitle", "A Morning Mercies devotion")),
            "DESCRIPTION": html.escape(meta["description"], quote=True),
            "PAGE_URL": page_url,
            "SHARE_IMAGE_URL": absolute_url(meta["share_image"]),
            "ASSET_PREFIX": "../../",
            "BODY_HTML": markdown_to_html(body_md),
            "AUTHOR": html.escape(meta["author"]),
        })
        (page_dir / "index.html").write_text(rendered, encoding="utf-8")
        entries.append({
            "title": meta["title"],
            "subtitle": meta.get("subtitle", "Morning Mercies"),
            "url": f"devotions/{slug}/",
            "day": meta.get("day", ""),
        })

    if not entries:
        raise ValueError("No devotion files found in content/devotions/")

    def day_number(entry: dict[str, str]) -> int:
        try:
            return int(entry.get("day") or 0)
        except ValueError:
            return 0

    entries.sort(key=day_number, reverse=True)
    items = []
    for entry in entries:
        items.append(
            '<li><a href="{url}"><div class="item-title">{title}</div>'
            '<div class="item-meta">{subtitle}</div></a></li>'.format(
                url=html.escape(entry["url"], quote=True),
                title=html.escape(entry["title"]),
                subtitle=html.escape(entry["subtitle"]),
            )
        )

    (OUT_DIR / "index.html").write_text(
        fill(index_template, {"DEVOTION_LIST": "\n".join(items)}),
        encoding="utf-8",
    )
    print(f"Built {len(entries)} devotion(s) into {OUT_DIR}")


if __name__ == "__main__":
    build()
