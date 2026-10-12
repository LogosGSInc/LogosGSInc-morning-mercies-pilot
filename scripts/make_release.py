"""Interactive packet helper. No cloud credentials or JSON editing required."""
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

def yes(prompt):
    return input(prompt + ' [yes/no]: ').strip().lower() == 'yes'

def main():
    title=input('Release title: ').strip()
    identifier=re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')
    kind=input('Type [song/podcast/video/promo]: ').strip()
    series=input('Series [Morning Mercies/On Watch]: ').strip()
    description=input('One-sentence description: ').strip()
    transcript=Path(input('Path to reviewed lyrics or transcript text file: ').strip()).read_text()
    output=Path('release-packets')/identifier
    output.mkdir(parents=True,exist_ok=True)
    record=dict(id=identifier,title=title,type=kind,series=series,description=description,transcript=transcript,
                status='approved',publish_at=datetime.now(timezone.utc).isoformat(),
                article_path=input('Companion article path (e.g. articles/the-lamb-holds-the-scroll/; blank for none): ').strip(),
                editorial_approved=yes('Has this content completed editorial acceptance?'))
    for medium,suffix in [('audio','.mp3'),('video','.mp4'),('poster',''),('captions','.vtt')]:
        value=input(f'Path to {medium} file (blank to skip): ').strip()
        if value:
            source=Path(value)
            filename=medium+(suffix or source.suffix.lower())
            shutil.copyfile(source,output/filename)
            record[medium+'_file']=filename
            if medium in {'audio','video'}:
                record[medium+'_qc_passed']=yes(f'Have you listened to/watched this final {medium} and checked Scripture and intelligibility?')
    if not record['editorial_approved'] or any(record.get(m+'_file') and not record.get(m+'_qc_passed') for m in ['audio','video']):
        record['status']='draft'
    (output/'release.json').write_text(json.dumps(dict(items=[record]),ensure_ascii=False,indent=2)+'\n')
    print('Packet:',output.resolve())
    print('Attach these files to a GitHub Release tagged abg-'+identifier+'.')
    print('Only publish the Release after final review. Draft packets are rejected by the importer.')

if __name__=='__main__': main()
