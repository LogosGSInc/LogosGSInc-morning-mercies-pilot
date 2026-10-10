# Authored by Grace — content catalog

Public catalog and daily publishing system for **Authored by Grace**, beginning with Morning Mercies. See [catalog publishing](docs/CATALOG-PUBLISHING.md) for twice-daily posts, media entries, draft handling, and migration notes.

## Daily workflow

1. Claude/reviewer produces one final canonical Markdown file.
2. Put it in `content/devotions/`.
3. Approve the finished entry, then merge its reviewed change to `main`.
4. GitHub Actions generates:
   - the warm-paper branded web devotion,
   - a unique 1200×630 social card,
   - a ready-to-copy social teaser text file,
   - the updated Morning Mercies home/archive page,
   - and deploys everything to GitHub Pages.

The `.md` file is source material only. Readers see generated HTML.

## Tomorrow's file

Copy `content/DEVOTION_TEMPLATE.md`, rename it, fill it, and place it under `content/devotions/`.

Example:

`content/devotions/2026-09-27-vengeance-belongs-to-god.md`

## Public routing

Facebook/social cards should link directly to each devotion, not the home page.

Example:

`https://logosgsinc.github.io/LogosGSInc-morning-mercies-pilot/devotions/why-you-keep-losing-the-same-battle/`

The site root features the newest released devotional and a searchable collection. Existing devotional URLs stay intact.

## Pages setup

Repository Settings → Pages → Build and deployment → Source → **GitHub Actions**.

## Approved house style and daily preparation

See [the publishing decisions](docs/MORNING-MERCIES-HOUSE-STYLE.md). Install dependencies with `python -m pip install -r requirements.txt`, then run `python build.py`. The build produces final PNG cards directly using bundled fonts and approved artwork; no separate SVG conversion is required.

Supply the exact card verse, reference, thematic line, and publication date in the canonical Markdown. Publish the prepared entry the next morning only after the author's release instruction. Never push main as part of afternoon preparation.

