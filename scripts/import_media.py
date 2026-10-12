"""Validate reviewed release assets, upload to R2, and persist their catalog records."""
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hub import validate_media, https_url

def asset(directory, name, suffixes):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
        raise ValueError("Asset names must be plain filenames")
    path = directory / name
    if not path.is_file() or path.suffix.lower() not in suffixes:
        raise ValueError(f"Missing asset or unsupported format: {name}")
    return path

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def inspect_media(path, medium):
    result = subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],
                            check=True,capture_output=True,text=True,timeout=120)
    info = json.loads(result.stdout)
    streams = info['streams']
    duration = float(info['format']['duration'])
    if duration <= 0:
        raise ValueError("Media duration must be positive")
    if medium == 'audio' and not any(s.get('codec_name') == 'mp3' for s in streams):
        raise ValueError("Audio must be an MP3")
    if medium == 'video':
        if not any(s.get('codec_name') == 'h264' and s.get('codec_type') == 'video' for s in streams):
            raise ValueError("Video must use H.264 in an MP4 container")
        if not any(s.get('codec_name') == 'aac' and s.get('codec_type') == 'audio' for s in streams):
            raise ValueError("Video must contain AAC audio")
    return round(duration)

def run(directory):
    import boto3
    base = https_url(os.environ['MEDIA_BASE_URL'].rstrip('/'))
    records = json.loads((directory / 'release.json').read_text())['items']
    if not isinstance(records, list) or not records:
        raise ValueError("release.json requires a nonempty items array")
    prepared = []
    seen = set()
    for source in records:
        r = {k:v for k,v in source.items() if not k.endswith('_file')}
        if r.get('id') in seen:
            raise ValueError("Duplicate media ID in release")
        seen.add(r.get('id'))
        uploads = []
        for medium, suffixes in [('audio',{'.mp3'}),('video',{'.mp4'}),('poster',{'.jpg','.jpeg','.png'}),('captions',{'.vtt'})]:
            name = source.get(medium + '_file')
            if not name:
                continue
            path = asset(directory, name, suffixes)
            sha = digest(path)
            key = f'{r.get("id", "")}/{sha[:16]}/{path.name}'
            r[medium+'_url'] = base + '/' + quote(key, safe='/')
            r[medium+'_sha256'] = sha
            r[medium+'_bytes'] = path.stat().st_size
            if medium in {'audio','video'}:
                r[medium+'_duration_seconds'] = inspect_media(path, medium)
            if medium == 'captions' and not path.read_text(encoding='utf-8-sig').startswith('WEBVTT'):
                raise ValueError("Captions must be UTF-8 WebVTT")
            mime = {'audio':'audio/mpeg','video':'video/mp4','captions':'text/vtt; charset=utf-8'}.get(medium) or mimetypes.guess_type(path.name)[0]
            uploads.append((path,key,mime))
        if not uploads or not any(source.get(k) for k in ('audio_file','video_file')):
            raise ValueError("A release must attach its media files")
        validate_media(r)
        if r.get('article_path') and not (ROOT / '_site' / r['article_path'] / 'index.html').is_file():
            raise ValueError("Publish the canonical companion article before importing its media")
        if r['status'] != 'approved':
            raise ValueError("Only reviewed, approved media may be imported")
        prepared.append((r, uploads))
    # Validate the entire batch before the first public upload.
    client = boto3.client('s3', endpoint_url=os.environ['R2_ENDPOINT'],
                         aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
                         aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'], region_name='auto')
    for r, uploads in prepared:
        for path,key,mime in uploads:
            client.upload_file(str(path),os.environ['R2_BUCKET'],key,ExtraArgs={
                'ContentType':mime,'CacheControl':'public, max-age=31536000, immutable',
                'Metadata':{'sha256':digest(path)}})
            head = client.head_object(Bucket=os.environ['R2_BUCKET'],Key=key)
            if head['ContentLength'] != path.stat().st_size or head.get('Metadata',{}).get('sha256') != digest(path):
                raise ValueError("Uploaded object failed verification")
            public = base + '/' + quote(key,safe='/')
            with urlopen(Request(public,headers={'Range':'bytes=0-1023'}),timeout=60) as response:
                if response.status not in {200,206}:
                    raise ValueError("Media URL is not publicly readable")
                response.read(1024)
        r['source_release_tag'] = os.environ.get('RELEASE_TAG','')
    target = ROOT / 'content/media'
    target.mkdir(parents=True,exist_ok=True)
    # Write only after all public media in the batch verified successfully.
    for r,_ in prepared:
        (target / (r['id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
        print('Registered media:',r['id'])

if __name__ == '__main__':
    run(Path(sys.argv[1]).resolve())
