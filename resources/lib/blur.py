# -*- coding: utf-8 -*-
"""Blurred copies of backdrops for the Fused Glass theme: the skin lays the copy under its frosted panels (through a
mask of the panels' shapes), so a panel shows the colours of the picture behind it, softly, as frosted glass does.
No Kodi imports."""
import hashlib
import io

SIZE = (640, 360)       # small: the skin stretches it to 1920 x 1080; blur hides the scaling
RADIUS = 14             # Gaussian blur radius at that size (about 42 px on screen)
QUALITY = 82


# 0.3.104 (skin 0.56.28) Expert settings: Panel blur (aeon.x.pblur) and Fanart blur (aeon.x.fblur) pick the radius
PANEL_RADIUS = {'off': None, 'light': 8, 'strong': 22}           # '' (Default): RADIUS
# 0.3.111 (skin 0.56.45) Library fanart blur: Off, -2 .. +2 ('' and z = 0, the old Light, the default since then);
# light / medium / strong are the old steps (moved to '' / p1 / p2 by migrate_fanblur)
FANART_RADIUS = {'off': None, 'm2': 1, 'm1': 2, '': 4, 'z': 4, 'p1': 9, 'p2': 16, 'light': 4, 'medium': 9, 'strong': 16}
FANBLUR_OLD = {'light': '', 'medium': 'p1', 'strong': 'p2'}
# 0.3.110 (skin 0.56.44) Aeon Glass's Panel blur (aeon.agblur): the menus' backdrop blurred, '' (Off): none
AG_RADIUS = {'light': 6, 'medium': RADIUS, 'strong': 24}


def panel_radius(step):
    """the panels' blur radius for a Panel blur step ('' / unknown: the default; 'off': None)"""
    return PANEL_RADIUS[step] if step in PANEL_RADIUS else RADIUS


def fanart_radius(step):
    """the library fanart's blur radius for a step (unknown: the default 0)"""
    return FANART_RADIUS.get(step, FANART_RADIUS[''])


def fanblur_new(value, view=False):
    """an old Library fanart blur value as a new one (None: nothing to change); a view's 0 is z ('' follows)"""
    if value not in FANBLUR_OLD:
        return None
    new = FANBLUR_OLD[value]
    return 'z' if view and not new else new


def menu_radius(fglass_frost, ag_step):
    """the radius of the menus' blurred backdrop: Fused Glass's Frost style the default, Aeon Glass its Panel blur step
    ('' / unknown: None, no blurred copy)"""
    if fglass_frost:
        return RADIUS
    return AG_RADIUS.get(ag_step)


def cache_name(source, radius=RADIUS):
    """File name of the blurred copy of a picture path (the default radius keeps the old names)."""
    name = hashlib.md5(source.encode('utf-8')).hexdigest()
    return name + ('.jpg' if radius == RADIUS else '_r%d.jpg' % radius)


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


def make(data, radius=RADIUS):
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
    image = image.filter(ImageFilter.GaussianBlur(radius))
    out = io.BytesIO()
    image.save(out, 'JPEG', quality=QUALITY)
    return out.getvalue()
