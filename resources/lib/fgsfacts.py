# -*- coding: utf-8 -*-
"""0.3.117 (skin 0.56.53): facts the Fused Glass style windows draw that Kodi does not hand the skin (user, 2026-11-20:
"these could be shown with the helper?").
Published on Home for the skin; the skin draws positions with ranges controls (<info> = "start%,end%,...").
  aeon.cp.white / aeon.cp.dark / aeon.cp.ok   colour picker: contrast of the colour in focus on white and on the
                                              style's dark ground ("2.0:1"), ok = 1 when the dark one reaches 4.5:1
  aeon.off.ranges / aeon.off.val              OSD audio / subtitle panel: the offset's place on a +-0.5 s ruler
  aeon.alb.ranges / aeon.alb.first / .id      Music information (album): one range per track, a gap between them;
                                              the first track alone (drawn in the accent)
  aeon.intm.ranges / aeon.intm.time / .path   Video information: the intermission's mark on the watched bar, from
                                              Skippy's chapters sidecar (a segment named Intermission / Intermezzo /
                                              Entr'acte); read only, Skippy is not touched
Picture info's strip of the folder: plugin ?info=picstrip&path=<picture> (plugin.py, strip())."""
import json
import os
import re
import xml.etree.ElementTree as ET

import xbmc
import xbmcgui
import xbmcvfs

HOME = 10000
DARK = (8, 9, 12)
SIDECARS = ('_chapters.xml', '-chapters.xml', '.chapters.xml')
NAMES = re.compile(r"intermission|intermezzo|entr.?acte|pause", re.I)
PICS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.webp', '.heic')


def rpc(method, params):
    return json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}))).get('result') or {}


def home():
    return xbmcgui.Window(HOME)


def luminance(rgb):
    out = []
    for c in rgb:
        c = c / 255.0
        out.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def contrast(hexa):
    """AARRGGBB / RRGGBB -> (on white, on the dark ground)"""
    h = (hexa or '').strip().lstrip('#')
    if len(h) == 8:
        h = h[2:]
    if not re.match(r'^[0-9a-fA-F]{6}$', h):
        return None
    rgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    lum = luminance(rgb)
    white = 1.05 / (lum + 0.05)
    dark = (lum + 0.05) / (luminance(DARK) + 0.05)
    return round(white, 1), round(dark, 1)


def seconds(text):
    m = re.search(r'(-?\d+(?:[.,]\d+)?)', text or '')
    return float(m.group(1).replace(',', '.')) if m else None


def offset_ranges(value, span=0.5):
    """the marker 1.2 % wide on a -span..+span ruler"""
    pct = max(0.0, min(100.0, (value + span) / (2 * span) * 100.0))
    a, b = max(0.0, pct - 0.6), min(100.0, pct + 0.6)
    return '%.2f,%.2f' % (a, b)


def album_ranges(durations, gap=0.35):
    total = float(sum(durations))
    if total <= 0:
        return '', ''
    out, at = [], 0.0
    for d in durations:
        end = at + d / total * 100.0
        out.append((at, max(at, end - gap)))
        at = end
    text = ','.join('%.2f,%.2f' % r for r in out)
    return text, '%.2f,%.2f' % out[0]


def clock(text):
    """Matroska chapter time HH:MM:SS.nnnnnnnnn -> seconds"""
    m = re.match(r'\s*(\d+):(\d+):(\d+(?:\.\d+)?)', text or '')
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None


def read_text(path):
    f = xbmcvfs.File(path)
    try:
        return f.read()
    finally:
        f.close()


def sidecar(video):
    if not video or video.startswith(('plugin://', 'http://', 'https://')):
        return None
    folder, name = os.path.split(video)
    base = os.path.splitext(name)[0]
    for end in SIDECARS:
        p = os.path.join(folder, base + end) if '://' not in folder else folder + '/' + base + end
        if xbmcvfs.exists(p):
            return p
    p = os.path.join(folder, 'chapters.xml') if '://' not in folder else folder + '/chapters.xml'
    return p if xbmcvfs.exists(p) else None


def intermission(video):
    """(start seconds, label) of the first chapter named like an intermission, or None"""
    path = sidecar(video)
    if not path:
        return None
    try:
        root = ET.fromstring(read_text(path))
    except Exception:
        return None
    for atom in root.iter('ChapterAtom'):
        names = ' '.join((s.text or '') for s in atom.iter('ChapterString'))
        if NAMES.search(names):
            start = clock((atom.findtext('ChapterTimeStart') or ''))
            if start is not None:
                return start, names.strip()
    return None


def hhmm(s):
    s = int(s)
    return '%d:%02d' % (s // 3600, (s % 3600) // 60)


class Facts(object):
    def __init__(self):
        self.last = {}

    def put(self, key, value):
        if self.last.get(key) != value:
            self.last[key] = value
            home().setProperty(key, value)

    def tick(self):
        cond = xbmc.getCondVisibility
        # colour picker
        if cond('Window.IsVisible(dialogcolorpicker)'):
            got = contrast(xbmc.getInfoLabel('Container(6).ListItem.Label2'))
            if got:
                self.put('aeon.cp.white', '%.1f:1' % got[0])
                self.put('aeon.cp.dark', '%.1f:1' % got[1])
                self.put('aeon.cp.ok', '1' if got[1] >= 4.5 else '')
        # OSD offset ruler
        if cond('Window.IsActive(osdaudiosettings)'):
            v = seconds(xbmc.getInfoLabel('Player.AudioDelay'))
        elif cond('Window.IsActive(osdsubtitlesettings)'):
            v = seconds(xbmc.getInfoLabel('Player.SubtitleDelay'))
        else:
            v = None
        if v is not None:
            self.put('aeon.off.ranges', offset_ranges(v))
            self.put('aeon.off.val', '%+.3f s' % v)
        # album bar
        if cond('Window.IsActive(musicinformation)'):
            w = home()
            aid = w.getProperty('aeon.mus.id')
            if w.getProperty('aeon.mus.type') == 'album' and aid.isdigit() and self.last.get('aeon.alb.id') != aid:
                songs = rpc('AudioLibrary.GetSongs', {'filter': {'albumid': int(aid)}, 'properties': ['duration', 'track', 'disc'],
                                                      'sort': {'method': 'track'}}).get('songs') or []
                rng, first = album_ranges([int(s.get('duration') or 0) for s in songs])
                self.put('aeon.alb.ranges', rng)
                self.put('aeon.alb.first', first)
                self.put('aeon.alb.id', aid)
        # intermission
        if cond('Window.IsActive(movieinformation)'):
            w = home()
            path = w.getProperty('aeon.vi.path')
            if path and self.last.get('aeon.intm.path') != path:
                self.put('aeon.intm.path', path)
                found = None
                try:
                    found = intermission(path)
                except Exception as error:
                    xbmc.log('[script.aeon.helper] intermission: %s' % error, xbmc.LOGINFO)
                total = seconds(w.getProperty('aeon.vi.secs')) or 0
                if found and total > 0 and found[0] < total:
                    pct = found[0] / total * 100.0
                    self.put('aeon.intm.ranges', '%.2f,%.2f' % (max(0.0, pct - 0.25), pct + 0.25))
                    self.put('aeon.intm.time', hhmm(found[0]))
                else:
                    self.put('aeon.intm.ranges', '')
                    self.put('aeon.intm.time', '')


def strip(path, around=8):
    """the pictures of the folder of `path`, at most `around` either side of it; the picture itself marked"""
    if not path:
        return []
    folder = path.rsplit('/', 1)[0] + '/' if '/' in path else os.path.dirname(path)
    try:
        dirs, files = xbmcvfs.listdir(folder)
    except Exception:
        return []
    pics = sorted(f for f in files if f.lower().endswith(PICS))
    name = path.rsplit('/', 1)[-1] if '/' in path else os.path.basename(path)
    at = pics.index(name) if name in pics else 0
    out = []
    for f in pics[max(0, at - around):at + around + 1]:
        full = folder + f if folder.endswith('/') else os.path.join(folder, f)
        item = xbmcgui.ListItem(label=f, offscreen=True)
        item.setArt({'thumb': full, 'icon': full})
        if f == name:
            item.setProperty('aeon.current', '1')
        out.append((full, item, False))
    return out
