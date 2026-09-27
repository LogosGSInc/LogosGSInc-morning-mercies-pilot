# Morning Mercies — Authored by Grace

Pilot publishing repository for **Morning Mercies — Authored by Grace: Witness for daily devotion**.

Each devotion is stored once as Markdown. GitHub Actions runs the deterministic `build.py` renderer, applies the shared Morning Mercies HTML/CSS template, and deploys the resulting static site to GitHub Pages.

## Tomorrow morning: where does the .md file go?

Put every final approved devotion in:

```
content/devotions/
```

Example:

```
content/devotions/2026-09-27-your-title.md
```

The reader never sees the Markdown file. After you commit it to `main`, GitHub Actions:

```
Markdown devotion
      ↓
build.py
      ↓
shared HTML template + shared CSS
      ↓
_site/devotions/<slug>/index.html
      ↓
GitHub Pages
```

Copy `content/DEVOTION_TEMPLATE.md` when starting a new devotion.

## First devotion

Source:

```
content/devotions/2026-09-26-ephesians-6-11.md
```

Public path after Pages is enabled:

```
https://logosgsinc.github.io/LogosGSInc-morning-mercies-pilot/devotions/why-you-keep-losing-the-same-battle/
```

## Enable Pages

Open **Settings → Pages → Build and deployment → Source → GitHub Actions**.

The included workflow will build and deploy automatically on each push to `main`.

## Repository structure

```
content/devotions/       final canonical devotion source
content/DEVOTION_TEMPLATE.md
templates/               reusable HTML shells
assets/css/              reusable visual system
assets/og/               social-preview artwork sources
assets/cover.svg         pilot series cover
build.py                 Markdown → branded HTML renderer
.github/workflows/       automated Pages build/deploy
```

## Design rule

Content and presentation stay separate. The devotion is canonical Markdown; the web presentation is reusable HTML/CSS. Changing the template later can restyle every devotion without rewriting the stories.
