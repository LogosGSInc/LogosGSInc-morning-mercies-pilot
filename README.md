# Authored by Grace

A Scripture, story, prayer, song, podcast, and video catalog built on the existing Morning Mercies publisher. GitHub Pages hosts articles and the catalog; Cloudflare R2 serves MP3/MP4 media.

## Website

Home · Read · Listen · Watch · Explore (Morning Mercies, On Watch, Previews, About, Contact).

Existing /devotions/<slug>/ links remain stable. New articles use /articles/<id>/; media uses /media/<id>/. The newest approved deep dive appears in the homepage feature panel; without video, the panel features the latest article. Set featured_media_id in site-config.json to pin a release.

The approved cover and original hero heading are retained. Daily updates change catalog content. Old pilot recruitment blocks are removed from generated pages.

## Build

    python -m pip install -r requirements.txt
    python -m unittest -v test_publishing test_hub
    python build.py
    python scripts/check_links.py

Output: _site/. The checked-in series-cover-v3.jpg is the exact approved cover; deployment also reconstructs and verifies it using the existing SHA-256 gate.

## Activate media once

1. Create a Cloudflare R2 bucket for public, reviewed publication assets. Keep private drafts elsewhere.
2. Connect a media custom domain, such as media.<your-domain>. R2's r2.dev URL is rate-limited and intended for development.
3. Give a scoped token object read/write access to this bucket. Store R2_ENDPOINT, R2_ACCESS_KEY_ID, and R2_SECRET_ACCESS_KEY in GitHub Actions secrets.
4. Set repository variables R2_BUCKET and MEDIA_BASE_URL (the HTTPS public media root). Optionally set WEBSITE_BASE_URL; the default is the existing Pages project address.
5. Set R2 CORS for the website origin: allow GET and HEAD, allow Range, and expose Content-Length, Content-Range, and Accept-Ranges. Add the future website origin when it changes. Captions use anonymous CORS.
6. Confirm Pages uses GitHub Actions. The media workflow needs permission to commit small media records to main. If branch protections prohibit this, use PR-based registration rather than disabling protections without review.

No credentials are checked in. Activation and end-to-end cloud verification remain outstanding.

## Upload a release

    python scripts/make_release.py

Answer the prompts and select finished files and reviewed lyrics/transcript. The helper writes a release-packets/<title>/ folder containing release.json and attachments.

1. Listen/watch the final render. Check quoted Scripture, pronunciation, intelligibility, and mix balance.
2. Publish a companion article first, if there is one. Give its internal path in the record; blank permits standalone media.
3. Create a draft GitHub Release with an abg- tag. Attach release.json and the generated MP3/MP4/poster/WebVTT files.
4. Review, then publish the Release. **Attachments become public on Release publication.** Upload cleared material only. Releases are operator intake; R2 is the streaming destination.
5. Watch “Upload reviewed audio and video” in Actions. It probes the files, checks approval flags, uploads hash-addressed objects, verifies length/source-hash metadata and public readability, commits records, then explicitly calls the Pages deployment.

The explicit call is necessary: GITHUB_TOKEN pushes do not trigger another Pages build.

Supported: MP3 audio; H.264/AAC MP4; JPG/PNG poster; UTF-8 WebVTT captions. Every release needs lyrics/transcript; video needs reviewed captions. Target deep dives at 5–7 minutes. No unfinished media links are published.

release.json contains an items array. One packet can contain several songs, a podcast, and a deep dive. The helper prepares one item; combine reviewed records under items for a batch. IDs are stable lowercase slugs.

Retry through Actions → Run workflow after fixing configuration. Identical file hashes reuse object keys. Upload verification failure prevents record publication; Git push failure prevents deployment. Objects uploaded before a later failure can remain; rerun from current main. No automatic deletion is performed.

## Articles and timing

Existing devotional Markdown/card metadata remain supported. The inherited builder publishes **all** files in content/devotions/ when pushed to main. Hold tomorrow's Markdown until release time.

New content/articles/ records require approved status, editorial_approved=true, and a timezone-aware publish_at timestamp. Drafts are excluded. The accepted On Watch article is staged as a **draft**. Set its timestamp and approved status when ready. The public body contains Article + Prayer + Field Order, excluding internal review records.

Future timestamps remain held until an eligible rebuild. **No unattended scheduler is configured.** Run the Pages workflow or push at release time. The upload helper uses the current UTC time for immediate publication.

## Contact and linking

Contact uses logosgs@proton.me through a mailto link, opening the visitor's email app. This is not a browser-submitted form. GitHub Pages does not run an email server or issue github.io mailboxes. Branded email requires an owned domain and separate email hosting.

Add verified Substack and social URLs to site-config.json. Empty settings are hidden. A future browser contact form needs a real endpoint and spam protection.

Promotional posts and Substack Notes point to the canonical website article; Substack is the temporary fallback when that page is unavailable. Do not host KDP Select ebook text.

## Verification limits

- Media storage and live upload/playback are not activated.
- Browser visual QA is unavailable in this environment. Responsive styling, keyboard controls, and static checks are implemented; device review remains.
- The site is a free editorial catalog. A checkout or primarily transaction-focused business requires suitable commercial hosting under GitHub Pages' restrictions.
- Podcast listening pages are included. Podcast RSS/directory distribution is a later milestone requiring show metadata and a square cover.

## Primary references

- [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
- [Large files](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)
- [Release asset limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- [GITHUB_TOKEN behavior](https://docs.github.com/en/actions/concepts/security/github_token)
- [R2 public buckets](https://developers.cloudflare.com/r2/buckets/public-buckets/)
- [Proton custom domain email](https://proton.me/support/custom-domain)
