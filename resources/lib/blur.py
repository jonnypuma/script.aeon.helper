# -*- coding: utf-8 -*-
"""Blurred copies of backdrops for the Fused Glass theme: the skin lays the copy under its frosted panels (through a
mask of the panels' shapes), so a panel shows the colours of the picture behind it, softly, as frosted glass does.
No Kodi imports."""
import hashlib
import io

SIZE = (640, 360)       # small: the skin stretches it to 1920 x 1080; blur hides the scaling
RADIUS = 14             # Gaussian blur radius at that size (about 42 px on screen)
QUALITY = 82


def cache_name(source):
    """File name of the blurred copy of a picture path."""
    return hashlib.md5(source.encode('utf-8')).hexdigest() + '.jpg'


def cover_box(size, target=SIZE):
    """The centred crop of a picture of the given size that has the target's shape (what aspectratio scale shows)."""
    w, h = size
    tw, th = target
    if w <= 0 or h <= 0:
        return None
    if w * th > h * tw:                 # wider than the target: cut the sides
        nw = int(round(h * tw / float(th)))
        left = (w - nw) // 2
        return left, 0, left + nw, h
    nh = int(round(w * th / float(tw)))
    top = (h - nh) // 2
    return 0, top, w, top + nh


def make(data):
    """JPEG bytes of the blurred, downscaled backdrop (b'' when the picture cannot be read)."""
    try:
        from PIL import Image, ImageFilter
        image = Image.open(io.BytesIO(data))
        image.draft('RGB', (SIZE[0] * 2, SIZE[1] * 2))      # JPEG: decode at a reduced size, much faster
        image = image.convert('RGB')
    except Exception:
        return b''
    box = cover_box(image.size)
    if not box:
        return b''
    image = image.crop(box).resize(SIZE, Image.BILINEAR)
    image = image.filter(ImageFilter.GaussianBlur(RADIUS))
    out = io.BytesIO()
    image.save(out, 'JPEG', quality=QUALITY)
    return out.getvalue()
