import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import build
import hub

class HubTests(unittest.TestCase):
    def record(self):
        return dict(id='faithful-and-true',title='Faithful and True',description='A companion song.',series='On Watch',
                    type='song',status='approved',publish_at='2026-10-11T09:00:00-05:00',transcript='Reviewed lyrics.',
                    audio_url='https://media.example.com/song.mp3',editorial_approved=True,audio_qc_passed=True)

    def test_unreviewed_or_future_media_is_not_ready(self):
        r = self.record()
        now = datetime(2026,10,11,13,0,tzinfo=timezone.utc)
        self.assertFalse(hub.ready(r,now))
        self.assertTrue(hub.ready(r,datetime(2026,10,11,15,0,tzinfo=timezone.utc)))
        r['status']='draft'
        self.assertFalse(hub.ready(r))

    def test_clearance_captions_and_url_requirements(self):
        r=self.record()
        hub.validate_media(r)
        for field in ('editorial_approved','audio_qc_passed'):
            bad=copy.deepcopy(r); bad[field]=False
            with self.assertRaises(ValueError): hub.validate_media(bad)
        bad=copy.deepcopy(r); bad['audio_url']='javascript:alert(1)'
        with self.assertRaises(ValueError): hub.validate_media(bad)
        bad=copy.deepcopy(r); bad.update(type='video',video_url='https://media.example.com/deep-dive.mp4',video_qc_passed=True)
        with self.assertRaisesRegex(ValueError,'captions'): hub.validate_media(bad)
        bad['captions_url']='https://media.example.com/deep-dive.vtt'
        hub.validate_media(bad)
        bad['article_path']='../../secrets/'
        with self.assertRaises(ValueError): hub.validate_media(bad)

    def test_static_hub_preserves_articles_and_omits_empty_embeds(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'site'
            with patch.object(build,'OUT_DIR',out):
                build.build()
                before={p.relative_to(out):p.read_text() for p in (out/'devotions').glob('*/index.html')}
                hub.build_hub(build)
                for path in before:
                    self.assertTrue((out/path).exists())
                    self.assertIn('aria-label="Main navigation"',(out/path).read_text())
                    self.assertNotIn('Request a pilot seat',(out/path).read_text())
                self.assertIn('logosgs@proton.me',(out/'contact/index.html').read_text())
                index=(out/'index.html').read_text()
                self.assertNotIn('<video',index)
                self.assertIn('The latest reading',index)
                self.assertTrue((out/'listen/index.html').exists())
                self.assertTrue((out/'watch/index.html').exists())
                self.assertEqual(len(json.loads((out/'catalog.json').read_text())),len(before))

    def test_html_is_escaped_in_players(self):
        r=self.record();r['title']='<script>alert(1)</script>'
        self.assertNotIn('<script>',hub.player(r))

    def test_media_release_builds_player_transcript_and_companion_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'_site'
            (root/'content/media').mkdir(parents=True)
            (root/'content/articles').mkdir(parents=True)
            (root/'site-config.json').write_text(json.dumps(dict(contact_email='logosgs@proton.me',substack_url='',featured_media_id='',social_links={})))
            meta,_=build.parse_front_matter(next(build.CONTENT_DIR.glob('*.md')).read_text())
            r=self.record()
            r.update(publish_at='2000-01-01T00:00:00Z',type='video',video_url='https://media.example.com/video.mp4',
                     captions_url='https://media.example.com/captions.vtt',video_qc_passed=True,
                     article_path=f'devotions/{meta["slug"]}/',transcript='## Transcript\n\n<script>untrusted</script>')
            (root/'content/media'/f'{r["id"]}.json').write_text(json.dumps(r))
            with patch.object(build,'OUT_DIR',out):
                build.build()
                with patch.object(build,'ROOT',root): hub.build_hub(build)
            index=(out/'index.html').read_text()
            self.assertIn('Featured deep dive',index)
            self.assertIn('preload="none"',index)
            detail=(out/'media'/r['id']/'index.html').read_text()
            self.assertIn('crossorigin="anonymous"',detail)
            self.assertIn('kind="captions"',detail)
            self.assertNotIn('<script>untrusted</script>',detail)
            self.assertIn('companion-media',(out/r['article_path']/'index.html').read_text())

if __name__=='__main__': unittest.main()
