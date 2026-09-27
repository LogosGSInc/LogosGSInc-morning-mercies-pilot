# Morning Mercies — Authored by Grace

Pilot publishing system for **Morning Mercies — Authored by Grace: Witness for daily devotion**.

## Daily workflow

1. Claude/reviewer produces one final canonical Markdown file.
2. Put it in `content/devotions/`.
3. Commit to `main`.
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

The site root explains the project, features the newest devotion, offers the Founding Design Partner pilot, and keeps the devotion archive.

## Pages setup

Repository Settings → Pages → Build and deployment → Source → **GitHub Actions**.
