# -*- coding: utf-8 -*-
"""0.3.118 (skin 0.56.53): facts for the round-3 Fused Glass style windows (canvas round 3, user 2026-11-20: "go
ahead building the last mockups").
Service tick (Facts.tick), published on Home:
  aeon.fb.c1 .. aeon.fb.c6, aeon.fb.n   file browser: the path in control 412 as crumbs (the last ones)
  aeon.peek.path / aeon.peek.count      file browser (450) / media source (10): the folder in focus and what is in it
  aeon.tv.mins                          text viewer: about how many minutes the text reads (230 words a minute)
Plugin lists (plugin.py):
  ?info=peek        up to six pictures from the folder in aeon.peek.path (pictures, else posters / folder art)
  ?info=sources&media=video|music|pictures   every source of that kind; the one named aeon.ms.name marked current
  ?info=substreams  the playing video's subtitles as cards: your languages first (Kodi's subtitle language setting),
                    then A-Z; label = language, label2 = SDH / FORCED / FULL, property code = ISO code for the flag
Script: RunScript(script.aeon.helper,setsub,<index>|off)."""
import json
import os
import re

import xbmc
import xbmcgui
import xbmcvfs

HOME = 10000
PICS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')
ART = ('poster.jpg', 'folder.jpg', 'cover.jpg', 'fanart.jpg', 'poster.png', 'folder.png')


def rpc(method, params):
    return json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}))).get('result') or {}


def home():
    return xbmcgui.Window(HOME)


def join(folder, name):
    return folder + name if folder.endswith(('/', '\\')) else folder + '/' + name


def crumbs(path, keep=6):
    parts = [p for p in re.split(r'[\\/]+', path or '') if p and not p.endswith(':')]
    return parts[-keep:]


def listing(folder):
    try:
        dirs, files = xbmcvfs.listdir(folder)
    except Exception:
        return [], []
    return sorted(dirs), sorted(files)


def peek_items(folder, limit=6):
    if not folder:
        return []
    dirs, files = listing(folder)
    out = [join(folder, f) for f in files if f.lower().endswith(PICS)][:limit]
    for d in dirs:
        if len(out) >= limit:
            break
        sub = join(folder, d) + '/'
        _, sf = listing(sub)
        for a in ART:
            if a in sf:
                out.append(join(sub, a))
                break
    return out[:limit]


class Facts(object):
    def __init__(self):
        self.last = {}

    def put(self, key, value):
        if self.last.get(key) != value:
            self.last[key] = value
            home().setProperty(key, value)

    def peek(self, path):
        if path == self.last.get('aeon.peek.path'):
            return
        self.put('aeon.peek.path', path or '')
        # 0.3.119: the counts apart (the skin draws them with icons) and a stamp that reloads the peek list
        self.stamp = getattr(self, 'stamp', 0) + 1
        dirs, files = listing(path) if path else ([], [])
        self.put('aeon.peek.count', '%d · %d' % (len(dirs), len(files)) if path else '')
        known = bool(path) and bool(dirs or files)      # nothing read (multipath, special, offline): no counts
        self.put('aeon.peek.dirs', str(len(dirs)) if known else '')
        self.put('aeon.peek.files', str(len(files)) if known else '')
        self.put('aeon.peek.stamp', str(self.stamp))

    def tick(self):
        cond = xbmc.getCondVisibility
        if cond('Window.IsVisible(filebrowser)'):
            parts = crumbs(xbmc.getInfoLabel('Control.GetLabel(412)'))
            for i in range(6):
                self.put('aeon.fb.c%d' % (i + 1), parts[i] if i < len(parts) else '')
            self.put('aeon.fb.n', str(len(parts)))
            if cond('Container(450).ListItem.IsFolder') and xbmc.getInfoLabel('Container(450).ListItem.Label') != '..':
                self.peek(xbmc.getInfoLabel('Container(450).ListItem.FolderPath'))
            else:
                self.peek('')
        elif cond('Window.IsVisible(mediasource)'):
            row = xbmc.getInfoLabel('Container(10).ListItem.Label')
            self.peek(row if ('/' in row or chr(92) in row) else '')   # not the 'Enter path...' row
            self.put('aeon.ms.name', xbmc.getInfoLabel('Control.GetLabel(12).index(1)') or xbmc.getInfoLabel('Control.GetLabel(12)'))
        # 0.3.119: Videos / Music Files (the plain list 50 in the Fused Glass style): the path as crumbs, a peek
        if (cond('Window.IsActive(videos)') or cond('Window.IsActive(music)')) and cond('Control.IsVisible(50)')                 and not cond('Window.IsVisible(filebrowser)') and not cond('Window.IsVisible(mediasource)'):
            path = xbmc.getInfoLabel('Container.FolderPath')
            parts = [] if path.startswith(('sources://', 'library://')) else crumbs(path, 4)
            for i in range(4):
                self.put('aeon.f50.c%d' % (i + 1), parts[i] if i < len(parts) else '')
            label = xbmc.getInfoLabel('Container(50).ListItem.Label')
            fp = xbmc.getInfoLabel('Container(50).ListItem.FolderPath')
            if cond('Container(50).ListItem.IsFolder') and label != '..' and not fp.startswith(('add', 'plugin://', 'addons://')):
                self.peek(fp)
            else:
                self.peek('')
        # 0.3.120: the keyboard in the Fused Glass style - library titles matching what is typed (aeon.kb.h1-3, aeon.kb.found)
        if cond('Window.IsVisible(virtualkeyboard)'):
            q = ' '.join((xbmc.getInfoLabel('Control.GetLabel(312).index(1)') or '').split())
            if q != self.last.get('kb.q'):
                self.last['kb.q'] = q
                hits, found = kb_hits(q) if len(q) >= 2 else ([], 0)
                for i in range(3):
                    h = hits[i] if i < len(hits) else {}
                    for k in ('label', 'year', 'art'):
                        self.put('aeon.kb.h%d.%s' % (i + 1, k), h.get(k, ''))
                self.put('aeon.kb.found', str(found) if hits else '')
        elif 'kb.q' in self.last:
            self.last.pop('kb.q', None)
        if cond('Window.IsVisible(textviewer)') and not self.last.get('tv.done'):
            words = len((xbmc.getInfoLabel('Control.GetLabel(5)') or '').split())
            if words:
                self.put('aeon.tv.mins', str(max(1, int(round(words / 230.0)))))
                self.last['tv.done'] = True
        elif not cond('Window.IsVisible(textviewer)'):
            self.last.pop('tv.done', None)


def kb_hits(q):
    """films and shows whose title holds q: up to three (films first), and how many there are in all"""
    flt = {'field': 'title', 'operator': 'contains', 'value': q}
    out, total = [], 0
    for method, key in (('VideoLibrary.GetMovies', 'movies'), ('VideoLibrary.GetTVShows', 'tvshows')):
        r = rpc(method, {'filter': flt, 'properties': ['year', 'art'], 'limits': {'start': 0, 'end': 3},
                         'sort': {'method': 'title', 'ignorearticle': True}})
        total += (r.get('limits') or {}).get('total', 0)
        for it in r.get(key) or []:
            art = it.get('art') or {}
            out.append({'label': it.get('label', ''), 'year': str(it.get('year') or ''), 'art': art.get('poster') or art.get('thumb') or ''})
    return out[:3], total


def kbset(which):
    """types a suggestion of the keyboard (h1-3 = a library title, s1-3 = a recent search) into its field"""
    if which.startswith('h'):
        text = home().getProperty('aeon.kb.h%s.label' % which[1:])
    else:
        text = home().getProperty('aeon.search.%s' % which[1:])
    if text:
        rpc('Input.SendText', {'text': text, 'done': False})


def peek_list():
    out = []
    for p in peek_items(home().getProperty('aeon.peek.path')):
        item = xbmcgui.ListItem(label=os.path.basename(p.rstrip('/')), offscreen=True)
        item.setArt({'thumb': p, 'icon': p})
        out.append((p, item, False))
    return out


def sources_list(media):
    current = home().getProperty('aeon.ms.name')
    out = []
    for s in rpc('Files.GetSources', {'media': media or 'video'}).get('sources') or []:
        item = xbmcgui.ListItem(label=s.get('label') or '', offscreen=True)
        item.setLabel2(s.get('file') or '')
        if current and s.get('label') == current:
            item.setProperty('aeon.current', '1')
        out.append((s.get('file') or '', item, False))
    return out


def preferred():
    v = rpc('Settings.GetSettingValue', {'setting': 'locale.subtitlelanguage'}).get('value') or ''
    return {v.lower()} if v else set()


def substreams():
    players = rpc('Player.GetActivePlayers', {})
    vid = [p for p in (players if isinstance(players, list) else []) if p.get('type') == 'video']
    if not vid:
        return []
    props = rpc('Player.GetProperties', {'playerid': vid[0]['playerid'], 'properties': ['subtitles', 'currentsubtitle', 'subtitleenabled']})
    cur = (props.get('currentsubtitle') or {}).get('index') if props.get('subtitleenabled') else None
    mine = preferred()
    rows = []
    for s in props.get('subtitles') or []:
        code = s.get('language') or ''
        name = xbmc.convertLanguage(code, xbmc.ENGLISH_NAME) or code or s.get('name') or '?'
        nm = (s.get('name') or '').lower()
        kind = 'SDH' if (s.get('isimpaired') or 'sdh' in nm or 'hearing' in nm) else ('FORCED' if (s.get('isforced') or 'forced' in nm) else 'FULL')
        rows.append((0 if name.lower() in mine or code.lower() in mine else 1, name, kind, code, s.get('index')))
    rows.sort(key=lambda r: (r[0], r[1].lower(), r[2]))
    home().setProperty('aeon.pf.submore', '+ %d' % (len(rows) - 17) if len(rows) > 17 else '')   # the File and season page shows 17 flags
    out = []
    for group, name, kind, code, index in rows:
        item = xbmcgui.ListItem(label=name, label2=kind, offscreen=True)
        item.setProperty('code', xbmc.convertLanguage(code, xbmc.ISO_639_2) or code)
        item.setProperty('mine', '1' if group == 0 else '')
        if index == cur:
            item.setProperty('aeon.current', '1')
        out.append(('plugin://script.aeon.helper/?info=noop', item, False))
        item.setProperty('index', str(index))
    return out


def audiostreams():
    """the playing file's sound streams in their own order: language (name, flag code), codec and channels; the one
    playing marked (aeon.current)"""
    players = rpc('Player.GetActivePlayers', {})
    vid = [p for p in (players if isinstance(players, list) else []) if p.get('type') == 'video']
    if not vid:
        return []
    props = rpc('Player.GetProperties', {'playerid': vid[0]['playerid'], 'properties': ['audiostreams', 'currentaudiostream']})
    cur = (props.get('currentaudiostream') or {}).get('index')
    chans = {1: '1.0', 2: '2.0', 3: '2.1', 6: '5.1', 7: '6.1', 8: '7.1'}
    out = []
    for a in props.get('audiostreams') or []:
        code = a.get('language') or ''
        name = xbmc.convertLanguage(code, xbmc.ENGLISH_NAME) or code or '?'
        c = (a.get('codec') or '').lower()
        codec = {'truehd': 'TrueHD', 'eac3': 'E-AC3', 'dtshd_ma': 'DTS-HD MA', 'dtshd_hra': 'DTS-HD HRA', 'opus': 'Opus'}.get(c, c.upper())
        detail = '  ·  '.join(x for x in (codec, chans.get(a.get('channels'), str(a.get('channels') or '')), a.get('name') or '') if x)
        item = xbmcgui.ListItem(label=name, label2=detail, offscreen=True)
        item.setProperty('code', xbmc.convertLanguage(code, xbmc.ISO_639_2) or code)
        if a.get('index') == cur:
            item.setProperty('aeon.current', '1')
        out.append(('plugin://script.aeon.helper/?info=noop', item, False))
    return out


def setsub(arg):
    players = rpc('Player.GetActivePlayers', {})
    vid = [p for p in (players if isinstance(players, list) else []) if p.get('type') == 'video']
    if not vid:
        return
    if arg == 'off':
        rpc('Player.SetSubtitle', {'playerid': vid[0]['playerid'], 'subtitle': 'off'})
    elif arg.isdigit():
        rpc('Player.SetSubtitle', {'playerid': vid[0]['playerid'], 'subtitle': int(arg), 'enable': True})
