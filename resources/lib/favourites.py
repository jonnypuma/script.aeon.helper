# -*- coding: utf-8 -*-
"""Kodi's favourites for Home > Favourites (skin 0.32.0): what each one is, the group it belongs to and the builtin that
opens it. Works on the dicts of JSON-RPC Favourites.GetFavourites (type, title, path, window, windowparameter,
thumbnail). No Kodi imports."""
import re

KINDS = ('all', 'video', 'music', 'addons')

VIDEO_EXT = ('.mkv', '.mp4', '.m4v', '.avi', '.mov', '.wmv', '.ts', '.m2ts', '.mpg', '.mpeg', '.iso', '.strm', '.webm', '.vob')
AUDIO_EXT = ('.mp3', '.flac', '.m4a', '.aac', '.ogg', '.opus', '.wav', '.wma', '.ape', '.alac', '.dsf', '.cue')
VIDEO_WINDOWS = ('videos', '10025', 'tvchannels', 'tvguide', 'tvrecordings', 'tvtimers', 'tvsearch', 'videoplaylist',
                 '10700', '10701', '10702', '10703', '10028', 'movieinformation', 'fullscreenvideo')
MUSIC_WINDOWS = ('music', '10502', 'radiochannels', 'radioguide', 'radiorecordings', 'musicplaylist', '10500',
                 '10703', 'musicinformation', 'visualisation')
ADDON_WINDOWS = ('programs', '10001', 'addonbrowser', '10040', 'pictures', '10002')

LIBRARY = (
    (re.compile(r'videodb://tvshows/titles/(\d+)'), 'video', 'tvshow'),
    (re.compile(r'videodb://movies/sets/(\d+)'), 'video', 'set'),
    (re.compile(r'videodb://movies/titles/(\d+)'), 'video', 'movie'),
    (re.compile(r'musicdb://albums/(\d+)'), 'music', 'album'),
    (re.compile(r'musicdb://artists/(\d+)'), 'music', 'artist'),
)


def target(fav):
    """The path a favourite points at (media: its file, window: the window's parameter)."""
    return (fav.get('path') or fav.get('windowparameter') or '').strip().strip('"')


def classify(fav):
    """(group, what, dbid): group video / music / addons / other; what tvshow / set / movie / album / artist / channel /
    file / song / addon / folder / window; dbid an int for library items, else 0."""
    kind = (fav.get('type') or '').lower()
    path = target(fav)
    low = path.lower()
    for pattern, group, what in LIBRARY:
        found = pattern.search(low)
        if found:
            return group, what, int(found.group(1))
    if kind in ('script', 'androidapp'):
        return 'addons', 'addon', 0
    if low.startswith('pvr://channels/tv') or low.startswith('pvr://channels'):
        return ('music' if '/radio/' in low else 'video'), 'channel', 0
    if low.startswith('plugin://plugin.video') or low.startswith('plugin://plugin.audio') or low.startswith('plugin://plugin.program'):
        group = 'video' if '.video' in low else ('music' if '.audio' in low else 'addons')
        return group, 'addon', 0
    if low.startswith('plugin://') or low.startswith('addons://'):
        return 'addons', 'addon', 0
    if kind == 'media':
        if low.endswith(AUDIO_EXT) or low.startswith('musicdb://'):
            return 'music', 'song', 0
        if low.endswith(VIDEO_EXT) or low.startswith('videodb://'):
            return 'video', 'file', 0
        return 'other', 'file', 0
    if kind == 'window':
        window = (fav.get('window') or '').lower()
        if window in VIDEO_WINDOWS or low.startswith('videodb://'):
            return 'video', 'folder', 0
        if window in MUSIC_WINDOWS or low.startswith('musicdb://'):
            return 'music', 'folder', 0
        if window in ADDON_WINDOWS:
            return 'addons', 'folder', 0
        return 'other', 'window', 0
    return 'other', 'window', 0


def wanted(favs, kind):
    """(index, favourite) pairs in the group asked for ('all' or unknown: every one), in Kodi's order."""
    kind = kind if kind in KINDS else 'all'
    return [(i, f) for i, f in enumerate(favs or ()) if kind == 'all' or classify(f)[0] == kind]


def builtin(fav):
    """The builtin that opens a favourite, as Kodi's Favourites window does ('' when it cannot be opened)."""
    kind = (fav.get('type') or '').lower()
    path = target(fav)
    if kind == 'media' and path:
        return 'PlayMedia("%s")' % path
    if kind == 'window' and fav.get('window'):
        if path:
            return 'ActivateWindow(%s,"%s",return)' % (fav['window'], path)
        return 'ActivateWindow(%s)' % fav['window']
    if kind == 'script' and path:
        return 'RunScript("%s")' % path
    if kind == 'androidapp' and path:
        return 'StartAndroidActivity("%s")' % path
    return ''
