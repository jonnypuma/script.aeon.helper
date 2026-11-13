# -*- coding: utf-8 -*-
"""Title, year and scraper id of every film and show of the library, kept in the add-on's data folder.

Online lists are matched against it to tell what is in the library. Reading thousands of titles takes several
seconds, so it is done in the background (service start, after a video scan) in chunks."""
import json
import os
import time

import xbmc
import xbmcvfs

CHUNK = 500
MAX_AGE = 7 * 24 * 3600
KINDS = (('movie', 'VideoLibrary.GetMovies', 'movies', 'movieid'), ('tv', 'VideoLibrary.GetTVShows', 'tvshows', 'tvshowid'))


def path():
    folder = xbmcvfs.translatePath('special://profile/addon_data/script.aeon.helper/')
    if not xbmcvfs.exists(folder):
        xbmcvfs.mkdirs(folder)
    return os.path.join(folder, 'videos.json')


def rpc(method, params):
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return json.loads(xbmc.executeJSONRPC(request)).get('result') or {}


def load():
    """{'movie': [entry, ...], 'tv': [...]} with entries shaped for resources.lib.online.index, or None."""
    try:
        with open(path(), 'r') as handle:
            data = json.load(handle)
    except (IOError, OSError, ValueError):
        return None
    if time.time() - float(data.get('time') or 0) > MAX_AGE:
        return None
    return data.get('library') or None


def drop():
    try:
        os.remove(path())
    except OSError:
        pass


def build(monitor=None):
    library = {}
    for kind, method, key, idkey in KINDS:
        entries = []
        start = 0
        while True:
            reply = rpc(method, {'properties': ['title', 'year', 'imdbnumber'], 'limits': {'start': start, 'end': start + CHUNK}})
            chunk = reply.get(key) or []
            for item in chunk:
                number = str(item.get('imdbnumber') or '')
                # films: the scraper's default id is a TMDb id when it is a plain number (an IMDb id starts with tt).
                # shows: the default id is usually a TVDB number, so shows are matched by title and year.
                entries.append({'dbid': item[idkey], 'title': item.get('title') or item.get('label') or '', 'year': item.get('year') or 0,
                                'uniqueid': {'tmdb': number} if kind == 'movie' and number.isdigit() else {}})
            start += CHUNK
            if not chunk or start >= (reply.get('limits') or {}).get('total', 0):
                break
            if monitor is not None and monitor.waitForAbort(0.3):
                return None
        library[kind] = entries
    try:
        with open(path(), 'w') as handle:
            json.dump({'time': time.time(), 'library': library}, handle)
    except (IOError, OSError):
        pass
    return library
