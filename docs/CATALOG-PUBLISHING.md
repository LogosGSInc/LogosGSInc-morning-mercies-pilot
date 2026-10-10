# Authored by Grace catalog

This replaces the pilot homepage with a public catalog in the existing repository. Existing devotional URLs and approved artwork remain intact. The old reader invitation is replaced on both homepage and devotional pages.

## Daily work

Keep one `main` publishing branch. Each piece is a separate file; dates are filenames, not permanent branches. Use short review branches for batches of changes, then merge the reviewed work. A merged change rebuilds the entire catalog and deploys it through the existing GitHub Actions workflow.

Morning Mercies Markdown lives in `content/devotions/`. It continues to generate a page, a 1200 × 630 Scripture card, and a social caption. New posts should supply:

```
publish_date: "2026-10-09"
publish_at: "2026-10-09T08:00:00-05:00"
status: "draft"
```

Change `status` to `published` only when approved. Two posts on one date have distinct slugs and publication times. Store the actual UTC offset: Chicago is -05:00 during daylight time and -06:00 during standard time. Existing date-only posts retain their archive order and use local midnight.

Published future entries are omitted until their publication time. They appear on the next build after that time. No clock schedule or automatic content generation is enabled. For twice-daily releases, merge the approved morning and afternoon content when ready. A push or manual run rebuilds the site.

To view drafts locally: `INCLUDE_DRAFTS=1 python build.py`. Do not set this variable in deployment jobs. The PR checks the production build first, then creates a separate review artifact including visibly labeled draft catalog entries. That review artifact is never deployed.

## Music, spoken audio, video, downloads

Each released item has one JSON file in `content/catalog/`. Start from `content/CATALOG_ITEM_TEMPLATE.json`, outside that scanned folder. Allowed types: `music`, `audio`, `video`, `download`, `devotional`. Supply a real HTTPS `external_url` to the finished public asset. The template defaults to draft. Only released formats appear in the filter bar. Broken/placeholder URLs and unknown statuses fail validation when released.

This version links to externally hosted media rather than embedding untested player providers. It does not publish lyrics or production prompts by accident. NotebookLM production prompts and the complete uploaded production pack remain outside this public repository.

Praying Through Scripture, service-focused devotionals, and children's material can become series when their first reviewed item is ready. No empty category pages are created.

## Day seven source

The uploaded content batch seven is draft entry 12 in the existing devotional archive. Its long-form story is preserved, with its prayer, Scripture references, fiction note, and safety statement. Its morning card uses the full Philippians 4:9 KJV quotation. Both source forms are retained in one canonical Markdown file; private video/audio prompts and unreleased songs are excluded.

Before releasing it, resolve the source's developmental review hold and inspect its finished card. Distribution Block F's related links map to existing devotional pages. Finished song/audio/video links and sign-up provider were not supplied and are not invented.

## Before replacing the live homepage

Review the catalog and clear the content hold separately. Confirm PR build checks, inspect desktop and phone layouts, verify existing devotional links, and verify the Pages deployment after merging. The PR does not deploy or unpublish the current live site. Removing pilot marketing does not delete prior content.

## Membership and payments

This static catalog is public. Paid content must live behind an actual hosted membership service; hidden links or a JavaScript password are not access control. Subscription and storefront buttons are added only after real destination URLs and the offer are selected.
