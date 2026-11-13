# -*- coding: utf-8 -*-
"""Art shapes (no Kodi imports): which library pictures have the wrong shape for their art type, and which picture in
the same folder could stand in for one.

Kodi takes local art by file name only. A folder with both season06-poster.jpg (a real 2:3 poster) and
season06-poster.png (a 500 x 281 landscape picture) gives the season the .png on every refresh, because the file
listed last wins. Nothing checks the shape."""

try:
    from urllib.parse import unquote
except ImportError:                      # Python 2 (not used by Kodi 19+)
    from urllib import unquote

# art type -> (lowest, highest) width / height that fits. A 2:3 poster is 0.67, a 16:9 picture 1.78, a banner 5.4.
SHAPES = {
    'poster': (0.4, 0.9),
    'keyart': (0.4, 0.9),
    'banner': (2.5, 12.0),
    'landscape': (1.2, 2.6),
    'fanart': (1.2, 2.6),
}
IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.tbn', '.bmp', '.gif')


def checked(art_type):
    return art_type in SHAPES


def fits(art_type, width, height):
    """True when a width x height picture has the shape art_type needs (types without a rule always fit)."""
    if art_type not in SHAPES:
        return True
    if not width or not height:
        return True                      # unknown size: leave it alone
    low, high = SHAPES[art_type]
    return low <= float(width) / float(height) <= high


def unwrap(url):
    """'image://nfs%3a%2f%2fhost%2fShow%2fposter.jpg/' -> 'nfs://host/Show/poster.jpg'; other paths as they are."""
    if url.startswith('image://'):
        url = unquote(url[len('image://'):])
        if url.endswith('/'):
            url = url[:-1]
    return url


def is_local(path):
    """A file Kodi reads from a share or disk (not a web address or a picture inside another file)."""
    low = path.lower()
    if not low or low.startswith(('http://', 'https://', 'image://', 'video@', 'music@', 'special://temp')):
        return False
    return low.endswith(IMAGE_EXTS)


def split(path):
    """(folder with its separator, file name) for nfs://, smb:// and local paths."""
    cut = max(path.rfind('/'), path.rfind('\\'))
    return path[:cut + 1], path[cut + 1:]


def stem(name):
    dot = name.rfind('.')
    return name[:dot] if dot > 0 else name


def ext_rank(name):
    """Order to try pictures of the same name in: .jpg first, then .png, ..."""
    ext = name[name.rfind('.'):].lower() if '.' in name else ''
    return (IMAGE_EXTS.index(ext) if ext in IMAGE_EXTS else len(IMAGE_EXTS), name)


def type_from_name(name):
    """The art type a local picture's file name says it is ('' when it does not say): season06-poster.png -> poster,
    folder.jpg -> poster, Heat.1995-banner.jpg -> banner, fanart12.jpg -> fanart."""
    base = stem(name).lower()
    if base == 'folder':
        return 'poster'
    for art_type in ('poster', 'keyart', 'banner', 'landscape'):
        if base == art_type or base.endswith('-' + art_type):
            return art_type
    tail = base.rsplit('-', 1)[-1]
    if tail.startswith('fanart') and tail[len('fanart'):].isdigit() or tail == 'fanart':
        return 'fanart'
    return ''


def candidates(path, art_type, names):
    """Pictures in the same folder that could stand in for path (an art_type picture): the same name with another
    extension (season06-poster.png -> season06-poster.jpg), and for a show / film poster.* also folder.*. In the
    order to try them; path itself is left out."""
    folder, name = split(path)
    base = stem(name).lower()
    bases = [base]
    if art_type == 'poster' and base == 'poster':
        bases.append('folder')
    found = []
    for want in bases:
        for other in sorted(names, key=ext_rank):
            if other == name or stem(other).lower() != want or not other.lower().endswith(IMAGE_EXTS):
                continue
            found.append(folder + other)
    return found


def best(art_type, measured):
    """measured: [(path, width, height)]; the largest picture that fits art_type, or None."""
    good = [(w * h, path) for path, w, h in measured if w and h and fits(art_type, w, h)]
    if not good:
        return None
    good.sort(key=lambda item: -item[0])
    return good[0][1]
