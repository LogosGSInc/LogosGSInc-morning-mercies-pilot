"""Fixed Morning Mercies artwork with daily typography rendered from metadata."""
from pathlib import Path
import re
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
SIZE = (1200, 630)
CREAM = '#ffe6bd'

def font(size, script=False, bold=False):
    name = 'GreatVibes-Regular.ttf' if script else 'CormorantGaramond.ttf'
    face = ImageFont.truetype(str(ASSETS / 'fonts' / name), size)
    if not script:
        face.set_variation_by_axes([700 if bold else 500])
    return face

def wrapped(draw, text, face, width):
    lines = []
    current = ''
    for word in text.split():
        candidate = (current + ' ' + word).strip()
        if draw.textlength(word, font=face) > width:
            raise ValueError('Card contains a word too wide to render')
        if current and draw.textlength(candidate, font=face) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines

def block(draw, text, center, top, width, height, maximum, minimum, script=False, bold=False):
    for size in range(maximum, minimum - 1, -1):
        face = font(size, script, bold)
        try:
            lines = wrapped(draw, text, face, width)
        except ValueError:
            continue
        step = int(size * 1.13)
        if len(lines) * step <= height:
            for i, line in enumerate(lines):
                x = center - draw.textlength(line, font=face) / 2
                y = top + i * step
                draw.text((x + 1, y + 2), line, font=face, fill='#02070c', anchor='lt')
                draw.text((x, y), line, font=face, fill=CREAM, anchor='lt')
            return
    raise ValueError(f'Card copy exceeds its readable layout: {text!r}')

def metadata(meta, short):
    result = dict(meta)
    if not result.get('card_verse'):
        # Existing posts begin with the root verse in an italic quoted paragraph.
        match = re.search(r'\*["“](.+?)["”]\*', short, re.S)
        if not match:
            raise ValueError(f"Missing card_verse for {meta['slug']}")
        result['card_verse'] = ' '.join(match.group(1).split())
    for key in ('card_title', 'card_scripture'):
        if not result.get(key):
            raise ValueError(f'Missing {key}')
    return result

def render(meta):
    if meta.get('card_image'):
        path = (ROOT / meta['card_image']).resolve()
        if not path.is_relative_to((ASSETS / 'cards').resolve()):
            raise ValueError('Approved card_image must be inside assets/cards')
        # Explicit human-approved finished art; never overwritten by a fallback.
        with Image.open(path) as source:
            return source.convert('RGB').resize(SIZE, Image.Resampling.LANCZOS)
    image = Image.open(ASSETS / 'cards' / 'house-background.png').convert('RGB').resize(SIZE, Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)
    block(draw, meta.get('series', 'Morning Mercies'), 480, 48, 740, 90, 76, 52, True)
    block(draw, meta['card_title'].upper(), 480, 170, 740, 145, 72, 42, bold=True)
    block(draw, meta['card_verse'], 480, 321, 800, 70, 30, 24)
    reference = meta['card_scripture']
    if 'KJV' not in reference.upper():
        reference += ' · ' + meta.get('translation', 'KJV')
    block(draw, reference.upper(), 480, 397, 790, 35, 27, 22)
    block(draw, meta.get('card_tagline', ''), 480, 457, 795, 45, 26, 22)
    block(draw, meta.get('brand', 'Authored by Grace'), 480, 495, 750, 55, 48, 38, True)
    block(draw, meta.get('tagline', 'Witness for daily devotion'), 480, 556, 740, 30, 26, 22, True)
    block(draw, meta['author'], 1020, 532, 220, 50, 38, 30, True)
    return image
