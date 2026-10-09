import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import build
import cards

class PublishingTests(unittest.TestCase):
    def test_complete_build_and_latest_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'site'
            with patch.object(build, 'OUT_DIR', out):
                build.build()
            sources = [p for p in build.CONTENT_DIR.glob('*.md') if build.visible(build.parse_front_matter(p.read_text())[0], p.name[:10])]
            latest = max(
                sources,
                key=lambda source: build.parse_front_matter(source.read_text())[0].get(
                    'publish_at', build.parse_front_matter(source.read_text())[0].get('publish_date', source.name[:10])
                ),
            )
            meta, _ = build.parse_front_matter(latest.read_text())
            slug = meta['slug']
            index = (out / 'index.html').read_text()
            self.assertIn(f'href="devotions/{slug}/">Read today', index)
            page = (out / 'devotions' / slug / 'index.html').read_text()
            self.assertIn(f'assets/og/{slug}.png', page)
            hebrews = (out / 'devotions' / 'hebrews-12-6-meaning-whom-the-lord-loveth-he-chasteneth' / 'index.html').read_text()
            self.assertIn('The bus from Montgomery', hebrews)
            self.assertNotIn('{{', page)
            self.assertNotIn('member library', index)
            self.assertEqual(len(list((out / 'assets' / 'og').glob('*.png'))), len(sources))
            for card in (out / 'assets' / 'og').glob('*.png'):
                with Image.open(card) as image:
                    self.assertEqual(image.size, (1200, 630))
            share = (out / 'share' / f'{slug}.txt').read_text()
            self.assertIn(f'devotions/{slug}/', share)
            exodus = (out / 'devotions' / 'exodus-20-8-meaning-why-god-commands-his-people-to-rest' / 'index.html').read_text()
            self.assertIn('Nate Ellison had not taken a day off', exodus)
            self.assertIn('Make my rest a quiet witness', exodus)
            self.assertNotIn('Before God ever told His people to rest', exodus)
            self.assertNotIn('Many of us still live with Egypt', exodus)

    def test_duplicate_slug_is_rejected(self):
        source = next(build.CONTENT_DIR.glob('*.md')).read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'a.md').write_text(source)
            (root / 'b.md').write_text(source)
            with patch.object(build, 'CONTENT_DIR', root), patch.object(build, 'OUT_DIR', root / 'site'):
                with self.assertRaisesRegex(ValueError, 'Duplicate slug'):
                    build.build()

    def test_unreadable_copy_fails_instead_of_truncating(self):
        meta, _ = build.parse_front_matter(next(build.CONTENT_DIR.glob('*.md')).read_text())
        meta.pop('card_image', None)
        meta['card_verse'] = 'Long scripture quotation ' * 100
        with self.assertRaisesRegex(ValueError, 'readable layout'):
            cards.render(meta)

    def test_approved_art_is_preserved(self):
        meta, _ = build.parse_front_matter((build.CONTENT_DIR / '2026-10-02-hebrews-12-6.md').read_text())
        output = cards.render(meta)
        with Image.open(build.ROOT / meta['card_image']) as image:
            expected = image.convert('RGB').resize(cards.SIZE, Image.Resampling.LANCZOS)
        self.assertEqual(output.tobytes(), expected.tobytes())

    def test_automatic_layout_is_repeatable(self):
        meta, _ = build.parse_front_matter((build.CONTENT_DIR / '2026-10-02-hebrews-12-6.md').read_text())
        meta.pop('card_image')
        self.assertEqual(cards.render(meta).tobytes(), cards.render(meta).tobytes())

if __name__ == '__main__':
    unittest.main()

