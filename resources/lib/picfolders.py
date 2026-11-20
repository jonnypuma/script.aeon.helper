# -*- coding: utf-8 -*-
"""Picture folders for Home > Pictures (skin 0.56.21, no Kodi imports).

Kodi has no picture library, so the helper walks the picture sources itself (JSON-RPC Files.GetDirectory, passed in as
listdir): every folder that holds photos or videos, a few levels deep, with how many of each, the dates of its oldest
and newest file (file times: Kodi gives no EXIF over JSON-RPC) and its newest pictures. Newest first, for the
"Newest folder" spotlight and the row of folders under the menu. The walk has limits (depth, folders, seconds) so a
large network share cannot hold Home up."""
import time

PICTURE_EXT = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.heif', '.tif', '.tiff', '.dng', '.cr2', '.cr3',
               '.nef', '.arw', '.orf', '.rw2', '.raf')
VIDEO_EXT = ('.mp4', '.m4v', '.mov', '.mkv', '.avi', '.mts', '.m2ts', '.3gp', '.webm', '.wmv', '.mpg', '.mpeg')
SKIP_PREFIX = ('addons://', 'plugin://')
THUMBS = 4


def kind(entry):
    """'folder', 'photo', 'video' or None for a Files.GetDirectory entry."""
    if entry.get('filetype') == 'directory':
        return 'folder'
    path = (entry.get('file') or '').lower()
    mime = (entry.get('mimetype') or '').lower()
    if mime.startswith('image/') or path.endswith(PICTURE_EXT):
        return 'photo'
    if mime.startswith('video/') or path.endswith(VIDEO_EXT):
        return 'video'
    return None


def usable(source):
    """A source the walk reads: not Kodi's "Picture add-ons" entry or a plugin."""
    path = source.get('file') or ''
    return bool(path) and not path.startswith(SKIP_PREFIX)


def walk(listdir, sources, max_depth=3, max_folders=400, seconds=20.0, clock=time.time):
    """Folders that hold photos or videos, newest first.

    listdir(path) -> the entries of a folder (Files.GetDirectory 'files', with lastmodified / mimetype);
    sources: Files.GetSources 'sources' (label, file). Depth 0 is the source itself (named after the source), its
    folders are depth 1. A folder's 'parent' is the folder above it, or the source's name for depth 1."""
    start = clock()
    found = []
    queue = []
    for src in sources:
        if usable(src):
            queue.append((src['file'], src.get('label') or '', '', 0, src.get('label') or ''))
    seen = 0
    while queue and seen < max_folders and clock() - start < seconds:
        path, name, parent, depth, source = queue.pop(0)
        seen += 1
        try:
            entries = listdir(path) or []
        except Exception:                                   # an unreachable share: skip it
            continue
        photos, videos, dates, pics = 0, 0, [], []
        for e in entries:
            k = kind(e)
            if k == 'folder':
                if depth < max_depth:
                    queue.append((e.get('file'), e.get('label') or '', name, depth + 1, source))
            elif k in ('photo', 'video'):
                stamp = e.get('lastmodified') or ''
                if stamp:
                    dates.append(stamp)
                if k == 'photo':
                    photos += 1
                    pics.append((stamp, e.get('file')))
                else:
                    videos += 1
        if photos or videos:
            pics.sort(reverse=True)
            found.append({'path': path, 'name': name, 'parent': parent, 'source': source, 'depth': depth,
                          'photos': photos, 'videos': videos, 'newest': max(dates) if dates else '',
                          'oldest': min(dates) if dates else '', 'pictures': [p for _s, p in pics[:THUMBS]]})
    return newest_first(found)


def newest_first(folders):
    return sorted(folders, key=lambda f: (f.get('newest') or '', f.get('name') or ''), reverse=True)


def _ymd(stamp):
    """'2025-08-12 14:32:00' -> (2025, 8, 12), or None."""
    try:
        y, m, d = stamp[:10].split('-')
        return int(y), int(m), int(d)
    except (ValueError, AttributeError):
        return None


def date_range(oldest, newest, months):
    """Dates of a folder's files, short: '12 Aug 2025', '12 - 19 Aug 2025', '28 Jul - 3 Aug 2025',
    '30 Dec 2024 - 2 Jan 2025'. months: the twelve short month names in the user's language."""
    a, b = _ymd(oldest), _ymd(newest)
    if not b:
        return ''
    if not a:
        a = b
    if a > b:
        a, b = b, a
    ma, mb = months[a[1] - 1], months[b[1] - 1]
    if a == b:
        return '%d %s %d' % (b[2], mb, b[0])
    if a[:2] == b[:2]:
        return '%d – %d %s %d' % (a[2], b[2], mb, b[0])
    if a[0] == b[0]:
        return '%d %s – %d %s %d' % (a[2], ma, b[2], mb, b[0])
    return '%d %s %d – %d %s %d' % (a[2], ma, a[0], b[2], mb, b[0])


def sources_key(sources):
    """What the cache is valid for: the usable sources' paths."""
    return '|'.join(sorted(s.get('file') or '' for s in sources if usable(s)))


def fresh(cache, sources, now, ttl=900):
    """The cached walk when it is for the same sources and younger than ttl seconds, else None."""
    if not isinstance(cache, dict):
        return None
    if cache.get('key') != sources_key(sources):
        return None
    if not isinstance(cache.get('folders'), list) or now - float(cache.get('at') or 0) > ttl:
        return None
    return cache['folders']


def spotlight(folders, months):
    """Home window properties for the "Newest folder" spotlight (aeon.pic.*): '' clears one."""
    props = {'name': '', 'parent': '', 'photos': '', 'videos': '', 'dates': '', 'folder': '', 'bg': '', 'more': '',
             'thumb1': '', 'thumb2': '', 'thumb3': '', 'thumb4': '', 'none': '' if folders else '1'}
    if not folders:
        return props
    f = folders[0]
    props.update({'name': f['name'], 'parent': f['parent'], 'photos': str(f['photos']) if f['photos'] else '',
                  'videos': str(f['videos']) if f['videos'] else '', 'dates': date_range(f['oldest'], f['newest'], months),
                  'folder': f['path'], 'bg': f['pictures'][0] if f['pictures'] else ''})
    for i, pic in enumerate(f['pictures'][:THUMBS]):
        props['thumb%d' % (i + 1)] = pic
    more = f['photos'] + f['videos'] - len(f['pictures'][:THUMBS])
    props['more'] = str(more) if more > 0 and len(f['pictures']) >= THUMBS else ''
    return props
