# -*- coding: utf-8 -*-
"""Facts about the video playing, for the Fused Glass information screen's "File and season" page (0.3.72).

RunScript(script.aeon.helper,playerfacts) when the screen opens publishes on Window(Home):
  aeon.pf.subs       subtitle languages, "Arabic, English x2, ..." (sorted, duplicates counted)
  aeon.pf.subcount   number of subtitle tracks
  aeon.pf.audio      audio tracks, "English · Portuguese"
  aeon.pf.audiocount number of audio tracks
  aeon.pf.size       file size, "7.9 GB"
  aeon.pf.file       the file name (no folder)
  aeon.pf.seasonpath videodb://tvshows/titles/<show>/<season>/ for a library episode (the page's season list)
Kodi has no infolabels for these while playing; everything comes from JSON-RPC."""
import json
import os

import xbmc
import xbmcgui

PROPS = ('aeon.pf.subs', 'aeon.pf.subcount', 'aeon.pf.audio', 'aeon.pf.audiocount', 'aeon.pf.size', 'aeon.pf.file', 'aeon.pf.seasonpath')


def rpc(method, params):
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return json.loads(xbmc.executeJSONRPC(request)).get('result') or {}


def language_name(code):
    if not code:
        return ''
    try:
        name = xbmc.convertLanguage(code, xbmc.ENGLISH_NAME)
    except Exception:
        name = ''
    return name or code


def counted(names):
    """['English', 'Arabic', 'English'] -> 'Arabic, English x2' (sorted)."""
    seen = {}
    for name in names:
        if name:
            seen[name] = seen.get(name, 0) + 1
    return ', '.join('%s x%d' % (n, c) if c > 1 else n for n, c in sorted(seen.items(), key=lambda kv: kv[0].lower()))


def playing_item(pid=None):
    """The library item playing: {'type': 'episode'|'movie'|..., 'id': n, 'tvshowid': n, 'season': n}."""
    if pid is None:
        players = [p for p in (rpc('Player.GetActivePlayers', {}) or []) if p.get('type') == 'video']
        if not players:
            return {}
        pid = players[0]['playerid']
    return rpc('Player.GetItem', {'playerid': pid, 'properties': ['tvshowid', 'season']}).get('item') or {}


def human_size(size):
    if not size:
        return ''
    gb = size / 1073741824.0
    if gb >= 1:
        return '%.1f GB' % gb
    return '%d MB' % round(size / 1048576.0)


def main():
    home = xbmcgui.Window(10000)
    for prop in PROPS:
        home.clearProperty(prop)
    players = [p for p in (rpc('Player.GetActivePlayers', {}) or []) if p.get('type') == 'video']
    if not players:
        return
    pid = players[0]['playerid']
    props = rpc('Player.GetProperties', {'playerid': pid, 'properties': ['subtitles', 'audiostreams']})
    subs = [language_name(s.get('language')) or s.get('name', '') for s in props.get('subtitles') or []]
    audio = [language_name(a.get('language')) or a.get('name', '') for a in props.get('audiostreams') or []]
    home.setProperty('aeon.pf.subs', counted(subs))
    home.setProperty('aeon.pf.subcount', str(len(subs)) if subs else '')
    home.setProperty('aeon.pf.audio', '  ·  '.join(a for a in audio if a))
    home.setProperty('aeon.pf.audiocount', str(len(audio)) if audio else '')
    item = playing_item(pid)
    if item.get('type') == 'episode' and item.get('tvshowid', -1) >= 0:
        home.setProperty('aeon.pf.seasonpath', 'videodb://tvshows/titles/%d/%d/' % (item['tvshowid'], item.get('season', 0)))
    path = xbmc.getInfoLabel('Player.FilenameAndPath')
    home.setProperty('aeon.pf.file', xbmc.getInfoLabel('Player.Filename'))
    if path and not path.startswith(('pvr://', 'plugin://', 'http://', 'https://')):
        details = rpc('Files.GetFileDetails', {'file': path, 'media': 'video', 'properties': ['size']}).get('filedetails') or {}
        home.setProperty('aeon.pf.size', human_size(details.get('size')))


def cast(dbtype, dbid):
    """Cast of a library episode / film as (name, role, photo); a photo only when it is a real path (the library can
    hold bare file names such as 'Morfydd_Clark.jpg' that Kodi cannot find)."""
    if not dbid:
        return []
    if dbtype == 'episode':
        details = rpc('VideoLibrary.GetEpisodeDetails', {'episodeid': dbid, 'properties': ['cast']}).get('episodedetails') or {}
    elif dbtype == 'movie':
        details = rpc('VideoLibrary.GetMovieDetails', {'movieid': dbid, 'properties': ['cast']}).get('moviedetails') or {}
    else:
        return []
    people = []
    for person in sorted(details.get('cast') or [], key=lambda c: c.get('order', 0)):
        thumb = person.get('thumbnail') or ''
        raw = thumb[len('image://'):] if thumb.startswith('image://') else thumb
        real = ('%3a' in raw.lower()[:12] or '://' in raw or raw.startswith('/') or os.path.isabs(raw))
        people.append((person.get('name', ''), person.get('role', ''), thumb if real else ''))
    return people
