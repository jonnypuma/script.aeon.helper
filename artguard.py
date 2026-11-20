# -*- coding: utf-8 -*-
"""Library art with the wrong shape (helper 0.3.66).

Kodi picks local art by file name only: with season06-poster.jpg (a real poster) and season06-poster.png (a landscape
picture) in one folder, every refresh gives the season the .png. This looks at the shape of posters, key art, banners,
landscapes and fanart; when one is wrong and a picture of the same name (another extension; for a poster.* also
folder.*) in the same folder has the right shape, the library gets that one instead. Files are never touched.

- after a library update: the service hands every updated film / show / season / episode to queue(); a worker checks
  them once Kodi has been quiet for a few seconds (Skin settings > Motion, memory, reset can switch this off)
- RunScript(script.aeon.helper,artcheck): the whole video library, with the background progress and a summary

Sizes come from Kodi's texture cache (it knows the size of every picture it has shown); others are read from the
start of the file."""
import io
import json
import threading
import time

import xbmc
import xbmcgui
import xbmcvfs

from resources.lib import artshape

SKIN = 'skin.aeon.fuse'
OFF = 'Skin.HasSetting(aeon.artguard.off)'
QUIET = 4.0                      # seconds without library updates before the queued items are checked

DETAILS = {
    'movie': ('VideoLibrary.GetMovieDetails', 'movieid', 'moviedetails', 'VideoLibrary.SetMovieDetails'),
    'tvshow': ('VideoLibrary.GetTVShowDetails', 'tvshowid', 'tvshowdetails', 'VideoLibrary.SetTVShowDetails'),
    'season': ('VideoLibrary.GetSeasonDetails', 'seasonid', 'seasondetails', 'VideoLibrary.SetSeasonDetails'),
}


def rpc(method, params=None):
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}})))
    return reply.get('result') or {}


def text(ident, fallback):
    return xbmc.getInfoLabel('$ADDON[%s %d]' % (SKIN, ident)) or fallback


def log(message):
    xbmc.log('[script.aeon.helper] art: %s' % message, xbmc.LOGINFO)


# ---------------------------------------------------------------- sizes

def cached_size(path):
    """(width, height) from Kodi's texture cache (its copy keeps the shape), or None."""
    for texture in rpc('Textures.GetTextures', {'filter': {'field': 'url', 'operator': 'is', 'value': path},
                                                'properties': ['sizes']}).get('textures') or []:
        for size in texture.get('sizes') or []:
            if size.get('width') and size.get('height'):
                return size['width'], size['height']
    return None


def read_size(path):
    """(width, height) read from the start of the file (Pillow needs only the header), or None."""
    try:
        from PIL import Image
    except ImportError:
        return None
    handle = xbmcvfs.File(path)
    try:
        data = b''
        for upto in (16384, 262144, 4194304):
            chunk = bytes(handle.readBytes(upto - len(data)))
            data += chunk
            try:
                return Image.open(io.BytesIO(data)).size
            except Exception:
                if len(data) < upto:            # the whole file was read and it is not a picture Pillow knows
                    return None
        return None
    except Exception:
        return None
    finally:
        handle.close()


def size_of(path, sizes):
    if path not in sizes:
        sizes[path] = cached_size(path) or read_size(path)
    return sizes[path]


# ---------------------------------------------------------------- one item

def folder_names(folder, listings):
    if folder not in listings:
        try:
            listings[folder] = xbmcvfs.listdir(folder)[1]
        except Exception:
            listings[folder] = []
    return listings[folder]


def check_art(kind, ident, art, label, sizes, listings):
    """Checks the item's art; fixes what it can. Returns ([(label, art type, new path, source)], [(label, art type)]);
    source is 'folder' (a picture of the same name in the same folder took its place) or 'cleared' (a season's slot
    was emptied: nothing in the folder fits, and the skin shows the show's own picture for an empty season slot; a
    media manager fills an empty slot later, while a filled one looks done to it)."""
    fixed, wrong = [], []
    for art_type, url in sorted(art.items()):
        if '.' in art_type or not artshape.checked(art_type):
            continue                                  # tvshow.poster etc. belong to the show, checked there
        path = artshape.unwrap(url)
        if not artshape.is_local(path):
            continue
        size = size_of(path, sizes)
        if not size or artshape.fits(art_type, *size):
            continue
        folder, _name = artshape.split(path)
        measured = []
        for other in artshape.candidates(path, art_type, folder_names(folder, listings)):
            other_size = size_of(other, sizes)
            if other_size:
                measured.append((other, other_size[0], other_size[1]))
        better = artshape.best(art_type, measured)
        if better:
            rpc(DETAILS[kind][3], {DETAILS[kind][1]: ident, 'art': {art_type: better}})
            log('%s %s: %s (%dx%d) -> %s' % (label, art_type, path, size[0], size[1], better))
            fixed.append((label, art_type, better, 'folder'))
        elif kind == 'season':
            rpc(DETAILS[kind][3], {DETAILS[kind][1]: ident, 'art': {art_type: None}})
            log("%s %s: %s (%dx%d) -> cleared (the skin shows the show's picture)" % (label, art_type, path, size[0], size[1]))
            fixed.append((label, art_type, '', 'cleared'))
        else:
            wrong.append((label, art_type))
    return fixed, wrong


def item_label(kind, details):
    if kind == 'season':
        season = details.get('season', 0)
        part = xbmc.getLocalizedString(20381) if season == 0 else '%s %d' % (xbmc.getLocalizedString(20373), season)
        return '%s · %s' % (details.get('showtitle', ''), part)
    return details.get('title') or details.get('label') or ''


def check_item(kind, ident, sizes, listings):
    method, key, field, _set = DETAILS[kind]
    props = ['art', 'title'] if kind != 'season' else ['art', 'season', 'showtitle']
    details = rpc(method, {key: ident, 'properties': props}).get(field) or {}
    return check_art(kind, ident, details.get('art') or {}, item_label(kind, details), sizes, listings)


def check_show(tvshowid, sizes, listings):
    fixed, wrong = check_item('tvshow', tvshowid, sizes, listings)
    for season in rpc('VideoLibrary.GetSeasons', {'tvshowid': tvshowid, 'properties': ['art', 'season', 'showtitle']}).get('seasons') or []:
        more = check_art('season', season['seasonid'], season.get('art') or {}, item_label('season', season), sizes, listings)
        fixed += more[0]
        wrong += more[1]
    return fixed, wrong


# ---------------------------------------------------------------- after library updates

class Guard(object):
    """Collects library updates (VideoLibrary.OnUpdate) and checks the items once Kodi has been quiet for QUIET s."""

    def __init__(self):
        self.lock = threading.Lock()
        self.movies, self.shows = set(), set()
        self.last = 0.0
        self.thread = None

    def queue(self, data):
        try:
            item = json.loads(data).get('item') or {}
        except Exception:
            return
        kind, ident = item.get('type'), item.get('id')
        if not ident or kind not in ('movie', 'tvshow', 'season', 'episode'):
            return
        with self.lock:
            if kind == 'movie':
                self.movies.add(ident)
            else:
                self.shows.add((kind, ident))
            self.last = time.time()
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.work, name='aeon-artguard')
            self.thread.start()

    def work(self):
        monitor = xbmc.Monitor()
        while not monitor.waitForAbort(1.0):
            with self.lock:
                if time.time() - self.last < QUIET or xbmc.getCondVisibility('Library.IsScanningVideo'):
                    continue
                movies, shows = self.movies, self.shows
                self.movies, self.shows = set(), set()
            if not movies and not shows:
                return
            if xbmc.getCondVisibility(OFF):
                continue
            self.run(movies, shows)

    def run(self, movies, shows):
        sizes, listings, fixed = {}, {}, []
        tvshows = set()
        for kind, ident in shows:
            if kind == 'tvshow':
                tvshows.add(ident)
            elif kind == 'season':
                tvshows.add((rpc('VideoLibrary.GetSeasonDetails', {'seasonid': ident, 'properties': ['tvshowid']}).get('seasondetails') or {}).get('tvshowid'))
            else:
                tvshows.add((rpc('VideoLibrary.GetEpisodeDetails', {'episodeid': ident, 'properties': ['tvshowid']}).get('episodedetails') or {}).get('tvshowid'))
        for ident in movies:
            fixed += check_item('movie', ident, sizes, listings)[0]
        for ident in tvshows:
            if ident:
                fixed += check_show(ident, sizes, listings)[0]
        if fixed:
            names = sorted({item[0].split(' · ')[0] for item in fixed})
            xbmcgui.Dialog().notification(text(32443, 'Library art') + ' · ' + ', '.join(names)[:60],
                                          text(32447, 'Fixed in the library: %d') % len(fixed),
                                          xbmcgui.NOTIFICATION_INFO, 6000)


# ---------------------------------------------------------------- the whole library

def art_name(art_type):
    known = {'poster': 20021, 'banner': 20020, 'fanart': 20445}
    return xbmc.getLocalizedString(known[art_type]) if art_type in known else art_type.capitalize()


def texture_sizes():
    """Every picture Kodi has shown, with its size: one call (about 30,000 pictures in a second and a half). Reading
    the whole library's art instead takes minutes."""
    sizes = {}
    for texture in rpc('Textures.GetTextures', {'properties': ['url', 'sizes']}).get('textures') or []:
        for size in texture.get('sizes') or []:
            if size.get('width') and size.get('height'):
                sizes[artshape.unwrap(texture.get('url', ''))] = (size['width'], size['height'])
                break
    return sizes


def owners(folder):
    """[(kind, id, details)] of the films and shows whose folder this is (a show's season art lies in its folder or in
    a season folder under it)."""
    for path in (folder, artshape.split(folder.rstrip('/\\'))[0]):          # shows first: the quicker question
        shows = rpc('VideoLibrary.GetTVShows', {'filter': {'field': 'path', 'operator': 'is', 'value': path},
                                                 'properties': ['art', 'title']}).get('tvshows') or []
        if shows:
            return [('tvshow', s['tvshowid'], s) for s in shows]
    return [('movie', m['movieid'], m) for m in rpc('VideoLibrary.GetMovies', {
        'filter': {'field': 'path', 'operator': 'is', 'value': folder}, 'properties': ['art', 'title']}).get('movies') or []]


def video_sources():
    """The video sources' folders: the cache also holds music (album covers are square folder.jpg pictures)."""
    return tuple(s['file'] for s in rpc('Files.GetSources', {'media': 'video'}).get('sources') or []
                 if s.get('file') and not s['file'].startswith(('addons://', 'plugin://')))


def check_all():
    """Skin settings > Motion, memory, reset > Check library art now. Starts from Kodi's texture cache: local pictures whose
    name says what they are (...-poster, folder, ...-banner, ...-landscape, ...-fanart, ...-keyart) and whose size has the
    wrong shape for it. The films and shows in those folders are then checked (seasons too) and fixed where a picture in
    the folder fits. Pictures Kodi has never shown are not in the cache: the check after library updates reads those."""
    log('library check started')
    progress = xbmcgui.DialogProgressBG()
    progress.create(text(32443, 'Library art'), '')
    sizes, listings, fixed, wrong = texture_sizes(), {}, [], []
    sources = video_sources()
    suspects = set()
    for path, (width, height) in sizes.items():
        if sources and path.startswith(sources) and artshape.is_local(path):
            art_type = artshape.type_from_name(artshape.split(path)[1])
            if art_type and not artshape.fits(art_type, width, height):
                suspects.add(artshape.split(path)[0])
    folders = sorted(suspects)
    monitor = xbmc.Monitor()
    seen = set()
    try:
        for done, folder in enumerate(folders):
            if monitor.abortRequested():
                return
            for kind, ident, item in owners(folder):
                if (kind, ident) in seen:
                    continue
                seen.add((kind, ident))
                label = item_label(kind, item)
                progress.update(int(100.0 * done / max(len(folders), 1)), text(32443, 'Library art'), label)
                if kind == 'tvshow':
                    more = check_show(ident, sizes, listings)
                else:
                    more = check_art(kind, ident, item.get('art') or {}, label, sizes, listings)
                fixed += more[0]
                wrong += more[1]
    finally:
        progress.close()
    log('library check: %d pictures known, %d folders with a picture of the wrong shape, %d fixed, %d still wrong'
        % (len(sizes), len(folders), len(fixed), len(wrong)))
    lines = []
    for source, ident, fallback in (('folder', 32444, 'Now uses a picture from the same folder that fits'),
                                    ('cleared', 32450, "Slot left empty: the skin shows the show's picture until season art is added")):
        these = [(label, art_type) for label, art_type, _p, src in fixed if src == source]
        if these:
            if lines:
                lines.append('')
            lines.append('[B]%s: %d[/B]' % (text(ident, fallback), len(these)))
            lines += ['%s · %s' % (label, art_name(art_type)) for label, art_type in these]
    if lines:
        # everything happens in Kodi's library: say so first (the files on disk are never touched)
        lines = ['[COLOR a3ffffff]%s[/COLOR]' % text(32451, "Only Kodi's library changed. Your files are untouched."), ''] + lines
    if wrong:
        if lines:
            lines.append('')
        lines.append('[B]%s: %d[/B]' % (text(32445, 'Wrong shape, nothing in the folder fits'), len(wrong)))
        lines += ['%s · %s' % (label, art_name(art_type)) for label, art_type in wrong]
    if not lines:
        lines.append(text(32446, 'Every picture has the right shape.'))
    xbmcgui.Dialog().textviewer(text(32443, 'Library art'), '[CR]'.join(lines))
