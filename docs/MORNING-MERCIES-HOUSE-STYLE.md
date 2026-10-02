# Morning Mercies publishing decisions

Approved by D. W. Smith on October 1, 2026. Applies to Morning Mercies / Authored by Grace only.

## Permanent visual direction

Midnight navy textured background; ornate hammered champagne-gold frame; luminous cream/gold typography; fine divider ornaments; warm lantern with illuminated smoke. Script is reserved for the series brand and signature. Scripture and the daily headline use readable serif type.

Hierarchy: Morning Mercies → daily devotional title → actual Scripture quotation → reference and translation → daily thematic line → Authored by Grace / Witness for daily devotion → D. W. Smith.

The approved finished Hebrews card is `assets/cards/hebrews-12-6-approved.png`. The reusable empty artwork is `assets/cards/house-background.png`. The approved book cover is `assets/cards/series-cover.png`. These are the references for future work. Never revert to the old silver border or make Authored by Grace dominate the daily title.

## Canonical content contract

Every new devotional supplies `publish_date` (YYYY-MM-DD), `card_title`, `card_scripture`, `card_verse` (exact displayed quotation), `card_tagline`, and `social_teaser`, in addition to the existing template fields. Card text is rendered deterministically from these fields. Copy that cannot fit at readable sizes fails the build instead of being silently truncated.

`card_image` is an optional explicit override for a finished card the author has approved. Hebrews uses this override to preserve the exact card approved on October 1. Future daily cards do not require image generation: omit that field and use the reusable plate and bundled fonts. If an approved card's text changes, remove the override or approve replacement art before publishing.

## Pilot cadence and release hold

October 1 preparation is for publication on the morning of October 2, 2026, America/Chicago. No push or deployment is authorized during preparation. The author supplies the next day's content in the afternoon; prepare and review it, then publish the next morning throughout the pilot. No fixed clock time or unattended publishing schedule has been selected.

Prepare content, card, generated page, and share caption before release. Hold the changes locally until the morning release instruction. A push to main triggers GitHub Actions and Pages. Check the deployment and public page/card before sharing; preparation previews are not live URLs.

After the pilot, use its results to decide between expanded website/book distribution (including KDP and D2D) and continued daily social publishing. No expansion or paid member library is promised by this decision.
