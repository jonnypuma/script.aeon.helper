# -*- coding: utf-8 -*-
"""0.3.111 (skin 0.56.45): the album track list in the music player controls (MusicOSD), the user's wish of
2026-11-18: the playing album's tracks on the right; arrows at the top step through the same artist's albums (the
arrow shows the name of the album it opens); OK on a track plays that album from that track.

Window(Home) properties for the skin:
    aeon.osd.alb.id / name / year     the album shown (its tracks: musicdb://albums/<id>/)
    aeon.osd.alb.prev / prev.name     the artist's album before it (by year), empty at the first
    aeon.osd.alb.next / next.name     the one after it, empty at the last
    aeon.osd.alb.artist               the artist whose albums the arrows step through
    aeon.osd.alb.playing              1 while the album shown is the one playing
The service sets them when a library song starts while the controls are open; RunScript(script.aeon.helper,osdalbum,
prev|next) steps; RunScript(script.aeon.helper,osdplay,<songid>) plays the album shown from that song.
The pure parts (order, neighbours) have no Kodi imports and are tested."""
import json

PROPS = ('id', 'name', 'year', 'prev', 'prev.name', 'next', 'next.name', 'artist', 'playing')


def order(albums):
    """[(albumid, title, year)] by year, then title (albums without a year last)"""
    return sorted(albums, key=lambda a: (a[2] or 9999, (a[1] or '').lower(), a[0]))


def neighbours(albums, shown):
    """(prev, next) of album id `shown` in the ordered list: (albumid, title) or None at the ends"""
    ids = [a[0] for a in albums]
    if shown not in ids:
        return None, None
    i = ids.index(shown)
    prev = albums[i - 1][:2] if i > 0 else None
    nxt = albums[i + 1][:2] if i + 1 < len(albums) else None
    return prev, nxt


def start_at(songs, songid):
    """the playlist position of songid in the album's songs [(songid, disc, track)] (disc, then track order)"""
    ordered = sorted(songs, key=lambda s: (s[1] or 0, s[2] or 0, s[0]))
    ids = [s[0] for s in ordered]
    return ids, (ids.index(songid) if songid in ids else 0)


# ------------------------------------------------------------------------------------------------- Kodi side
def _rpc(method, params=None):
    import xbmc
    request = {'jsonrpc': '2.0', 'id': 1, 'method': method}
    if params:
        request['params'] = params
    return json.loads(xbmc.executeJSONRPC(json.dumps(request))).get('result') or {}


def artist_albums(artistid):
    res = _rpc('AudioLibrary.GetAlbums', {'filter': {'artistid': int(artistid)}, 'properties': ['title', 'year']})
    return order([(a['albumid'], a.get('title') or a.get('label', ''), a.get('year') or 0) for a in res.get('albums', [])])


def publish(shown, artistid, playing_album):
    import xbmcgui
    home = xbmcgui.Window(10000)
    albums = artist_albums(artistid) if artistid else []
    found = [a for a in albums if a[0] == shown]
    if not found:
        res = _rpc('AudioLibrary.GetAlbumDetails', {'albumid': int(shown), 'properties': ['title', 'year']})
        det = res.get('albumdetails') or {}
        found = [(shown, det.get('title', ''), det.get('year') or 0)]
    prev, nxt = neighbours(albums, shown)
    values = {'id': str(shown), 'name': found[0][1], 'year': str(found[0][2] or ''),
              'prev': str(prev[0]) if prev else '', 'prev.name': prev[1] if prev else '',
              'next': str(nxt[0]) if nxt else '', 'next.name': nxt[1] if nxt else '',
              'artist': str(artistid or ''), 'playing': '1' if shown == playing_album else ''}
    for key in PROPS:
        home.setProperty('aeon.osd.alb.' + key, values[key])


def song_album(songid):
    """(albumid, the album artist's id) of a library song"""
    det = _rpc('AudioLibrary.GetSongDetails', {'songid': int(songid), 'properties': ['albumid', 'albumartistid', 'artistid']})
    song = det.get('songdetails') or {}
    artists = song.get('albumartistid') or song.get('artistid') or []
    return song.get('albumid'), (artists[0] if artists else None)


def follow_song(songid):
    """the service: a library song started (or the controls opened) - show its album"""
    albumid, artistid = song_album(songid)
    if albumid:
        publish(albumid, artistid, albumid)


def step(direction):
    """RunScript(script.aeon.helper,osdalbum,prev|next)"""
    import xbmc
    import xbmcgui
    home = xbmcgui.Window(10000)
    target = home.getProperty('aeon.osd.alb.' + ('prev' if direction == 'prev' else 'next'))
    if not target:
        return
    playing = None
    songid = xbmc.getInfoLabel('MusicPlayer.DBID')
    if songid.isdigit():
        playing = song_album(songid)[0]
    publish(int(target), home.getProperty('aeon.osd.alb.artist'), playing)


def play(songid):
    """RunScript(script.aeon.helper,osdplay,<songid>): the album shown, in disc and track order, from that song"""
    import xbmcgui
    home = xbmcgui.Window(10000)
    albumid = home.getProperty('aeon.osd.alb.id')
    if not (albumid.isdigit() and str(songid).isdigit()):
        return
    res = _rpc('AudioLibrary.GetSongs', {'filter': {'albumid': int(albumid)}, 'properties': ['disc', 'track']})
    songs = [(s['songid'], s.get('disc'), s.get('track')) for s in res.get('songs', [])]
    ids, pos = start_at(songs, int(songid))
    if not ids:
        return
    _rpc('Playlist.Clear', {'playlistid': 0})
    _rpc('Playlist.Add', {'playlistid': 0, 'item': [{'songid': i} for i in ids]})
    _rpc('Player.Open', {'item': {'playlistid': 0, 'position': pos}})
    home.setProperty('aeon.osd.alb.playing', '1')
