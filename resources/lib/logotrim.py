# -*- coding: utf-8 -*-
"""Clearlogos without their transparent border, so the skin can line them up (Low list: the logo starts on the line
of the first row). Most logo files are 800 x 310 with the artwork somewhere inside. No Kodi imports."""
import hashlib
import io

THRESHOLD = 16          # alpha at or below this counts as empty
MAX_SIDE = 800          # the skin shows logos at most 600 wide


def cache_name(source):
    """File name of the trimmed copy of a logo path."""
    return hashlib.md5(source.encode('utf-8')).hexdigest() + '.png'


def content_box(size, bbox):
    """The box to keep: the artwork's bounding box, or None when nothing would change (no border, or empty)."""
    if not bbox:
        return None
    left, top, right, bottom = bbox
    if right - left < 8 or bottom - top < 8:
        return None
    if (left, top, right, bottom) == (0, 0, size[0], size[1]):
        return None
    return left, top, right, bottom


def trim(data):
    """PNG bytes of the logo without its transparent border ('' when the picture cannot be read).
    A logo that has no border comes back unchanged in content, only re-saved."""
    try:
        from PIL import Image
        image = Image.open(io.BytesIO(data)).convert('RGBA')
    except Exception:
        return b''
    bbox = image.getchannel('A').point(lambda alpha: 255 if alpha > THRESHOLD else 0).getbbox()
    box = content_box(image.size, bbox)
    if box:
        image = image.crop(box)
    if max(image.size) > MAX_SIDE:
        scale = float(MAX_SIDE) / max(image.size)
        image = image.resize((max(1, int(image.size[0] * scale)), max(1, int(image.size[1] * scale))), Image.LANCZOS)
    out = io.BytesIO()
    image.save(out, 'PNG')
    return out.getvalue()
