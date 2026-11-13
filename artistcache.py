# -*- coding: utf-8 -*-
"""Genres of every album artist, kept in the add-on's data folder for the Similar artists row.

Asking Kodi for the song genres of thousands of artists takes many seconds, so it is done once in the background
(service start, after a music scan) in chunks, and the artist page reads the file."""
import json
import os
import time

import xbmc
import xbmcvfs

from resources.lib import similar

CHUNK = 400
MAX_AGE = 14 * 24 * 3600


def path():
    folder = xbmcvfs.translatePath('special://profile/addon_data/script.aeon.helper/')
    if not xbmcvfs.exists(folder):
        xbmcvfs.mkdirs(folder)
    return os.path.join(folder, 'artists.json')


def rpc(method, params):
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return json.loads(xbmc.executeJSONRPC(request)).get('result') or {}


def load():
    """[{'artistid', 'label', 'genres'}] or None when there is no usable file."""
    try:
        with open(path(), 'r') as handle:
            data = json.load(handle)
    except (IOError, OSError, ValueError):
        return None
    if time.time() - float(data.get('time') or 0) > MAX_AGE:
        return None
    return data.get('artists') or None


def drop():
    try:
        os.remove(path())
    except OSError:
        pass


def build(monitor=None):
    """Read all album artists chunk by chunk and save them. Returns the list (None when Kodi is shutting down)."""
    artists = []
    start = 0
    while True:
        reply = rpc('AudioLibrary.GetArtists', {'albumartistsonly': True, 'properties': ['genre', 'songgenres'],
                                                'limits': {'start': start, 'end': start + CHUNK}})
        chunk = reply.get('artists') or []
        for artist in chunk:
            artists.append({'artistid': artist['artistid'], 'label': artist.get('label') or '', 'genres': sorted(similar.genres_of(artist))})
        start += CHUNK
        if not chunk or start >= (reply.get('limits') or {}).get('total', 0):
            break
        if monitor is not None and monitor.waitForAbort(0.5):
            return None
    try:
        with open(path(), 'w') as handle:
            json.dump({'time': time.time(), 'artists': artists}, handle)
    except (IOError, OSError):
        pass
    return artists


def one(artistid):
    """A single artist straight from the library (quick): for artists that are not album artists."""
    details = rpc('AudioLibrary.GetArtistDetails', {'artistid': artistid, 'properties': ['genre', 'songgenres']}).get('artistdetails')
    if not details:
        return None
    return {'artistid': artistid, 'label': details.get('label') or '', 'genres': sorted(similar.genres_of(details))}


def similar_path(artistid):
    artists = load()
    if artists is None:
        artists = build() or []
    if not any(artist['artistid'] == artistid for artist in artists):
        extra = one(artistid)
        if extra:
            artists = artists + [extra]
    return similar.artists_path(similar.rank(artists, artistid))
