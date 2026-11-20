# -*- coding: utf-8 -*-
"""0.3.108 art of the focused title in a big library, at once.

Kodi loads a library list's art in the background from the top of the list: with 6,127 films a title in the middle
had no poster and no fanart for 30-40 seconds after the view opened (box, 2026-11-18). The user: "fix if possible
please!!". The library has the art; only the list item waits for it. So while a Videos or Music window is up, the
focused item's art is asked for over JSON-RPC (one call, in a worker thread, the newest focus wins) and published as
Window(Home).Property(aeon.fart.<kind>) with aeon.fart.type / aeon.fart.dbid naming the item. The skin's art variables
fall back to these only while the item's own art is still empty and the names match (_src/focusart_05642.py), so a
picture of another item never shows. ListItem labels are read through guiread (JSON-RPC on Kodi's main thread)."""
import json
import threading

import xbmc
import xbmcgui

# DBType -> (method, id parameter, result key)
METHODS = {
    'movie': ('VideoLibrary.GetMovieDetails', 'movieid', 'moviedetails'),
    'tvshow': ('VideoLibrary.GetTVShowDetails', 'tvshowid', 'tvshowdetails'),
    'season': ('VideoLibrary.GetSeasonDetails', 'seasonid', 'seasondetails'),
    'episode': ('VideoLibrary.GetEpisodeDetails', 'episodeid', 'episodedetails'),
    'set': ('VideoLibrary.GetMovieSetDetails', 'setid', 'setdetails'),
    'musicvideo': ('VideoLibrary.GetMusicVideoDetails', 'musicvideoid', 'musicvideodetails'),
    'album': ('AudioLibrary.GetAlbumDetails', 'albumid', 'albumdetails'),
    'artist': ('AudioLibrary.GetArtistDetails', 'artistid', 'artistdetails'),
}
KINDS = ('poster', 'fanart', 'thumb', 'landscape', 'clearlogo')
LIMIT = 3000


def pick(kind, art):
    """the pictures to publish from an item's art map (JSON-RPC names: season and episode art carries the show's as
    tvshow.*). The same fallbacks Kodi's list items have: a film's thumb is its poster, an episode's poster its season's."""
    art = art or {}

    def first(*names):
        for name in names:
            if art.get(name):
                return art[name]
        return ''
    if kind == 'episode':
        poster = first('season.poster', 'tvshow.poster')
    elif kind == 'season':
        poster = first('poster', 'tvshow.poster')
    else:
        poster = first('poster')
    return {'poster': poster,
            'fanart': first('fanart', 'tvshow.fanart', 'artist.fanart'),
            'thumb': first('thumb', 'poster'),
            'landscape': first('landscape', 'tvshow.landscape'),
            'clearlogo': first('clearlogo', 'tvshow.clearlogo')}


def request(kind, dbid):
    """(method, params, result key) for one item, or None for a kind the library has no details call for"""
    if kind not in METHODS or not str(dbid).isdigit() or int(dbid) <= 0:
        return None
    method, key, result = METHODS[kind]
    return method, {key: int(dbid), 'properties': ['art']}, result


class FocusArt(object):
    def __init__(self):
        self.seen = None            # (kind, dbid) of the focused item
        self.shown = None           # what the properties hold
        self.want = None
        self.cache = {}
        self.lock = threading.Lock()
        self.worker = None

    @staticmethod
    def rpc(method, params):
        try:
            got = json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})))
        except Exception:
            return {}
        return got.get('result') or {}

    def publish(self, item, pics):
        home = xbmcgui.Window(10000)
        for name in KINDS:
            home.setProperty('aeon.fart.' + name, (pics or {}).get(name, ''))
        home.setProperty('aeon.fart.type', item[0] if item else '')
        home.setProperty('aeon.fart.dbid', item[1] if item else '')
        self.shown = item

    def work(self):
        while True:
            with self.lock:
                job = self.want
                self.want = None
                if job is None:
                    self.worker = None
                    return
            call = request(*job)
            pics = {}
            if call:
                method, params, result = call
                pics = pick(job[0], (self.rpc(method, params).get(result) or {}).get('art'))
            with self.lock:
                if len(self.cache) > LIMIT:
                    self.cache.clear()
                self.cache[job] = pics
                current = self.seen
            if current == job:
                self.publish(job, pics)

    def tick(self):
        if not (xbmc.getCondVisibility('Window.IsActive(videos)') or xbmc.getCondVisibility('Window.IsActive(music)')):
            if self.shown:
                self.seen = None
                self.publish(None, None)
            return
        item = (xbmc.getInfoLabel('ListItem.DBType'), xbmc.getInfoLabel('ListItem.DBID'))
        if item == self.seen:
            return
        self.seen = item
        if request(*item) is None:
            return
        with self.lock:
            pics = self.cache.get(item)
            if pics is None:
                self.want = item
                if self.worker is None:
                    self.worker = threading.Thread(target=self.work)
                    self.worker.daemon = True
                    self.worker.start()
        if pics is not None:
            self.publish(item, pics)
