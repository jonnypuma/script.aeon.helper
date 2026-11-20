# -*- coding: utf-8 -*-
"""0.3.112 (skin 0.56.49): Skippy's segments as chapters on the player's bar (the user, 2026-11-18: "if the file itself
does not have chapters, it should still show chapters and timeline gaps on the OSD progress bar if Skippy has
identified them").

Skippy keeps the segments of the file it parsed in Window(Home).Property(skippy.parse_cache_snapshot.v1), a JSON text:
{"v": 1, "path": <file>, "segments": [{"start": s, "end": s, "label": ...}, ...]} (service.skippy
playback_segment_cache.py; written on every parse, emptied on a new video, not on stop: the path is checked). Every start
and end inside the file is a cut; cuts closer than MIN_PCT of the length (to each other or to either end) count once.
Published on Home, for the skin (cleared when no video plays):
  aeon.sk.ranges  the chapters as Kodi's Player.Chapters gives them (start %,end % per chapter: a ranges control's info)
  aeon.sk.count   how many chapters
  aeon.sk.part    the chapter playing (from 1)
The skin uses them only when the file has no chapters of its own (Includes_OSD.xml OSD_HasSkChapters)."""
import json

try:                                    # Python 3
    from urllib.parse import unquote
except ImportError:                     # pragma: no cover
    from urllib import unquote

SNAP = 'skippy.parse_cache_snapshot.v1'
MIN_PCT = 0.75
KEYS = ('aeon.sk.ranges', 'aeon.sk.count', 'aeon.sk.part')


def boundaries(segments, total, min_pct=MIN_PCT):
    """the cut points in seconds, sorted; near ones (and ones near either end) dropped"""
    try:
        total = float(total)
    except (TypeError, ValueError):
        return []
    if total <= 0:
        return []
    points = set()
    for seg in segments or []:
        if not isinstance(seg, dict):
            continue
        for key in ('start', 'end'):
            value = seg.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                points.add(float(value))
    gap = total * min_pct / 100.0
    out = []
    for point in sorted(points):
        if point <= gap or point >= total - gap:
            continue
        if out and point - out[-1] < gap:
            continue
        out.append(point)
    return out


def ranges(cuts, total):
    """'start%,end%,start%,end%,...' for the chapters between the cuts (empty without cuts)"""
    if not cuts or not total or total <= 0:
        return ''
    edges = [0.0] + list(cuts) + [float(total)]
    values = []
    for a, b in zip(edges, edges[1:]):
        values.append('%.5f' % (a * 100.0 / total))
        values.append('%.5f' % (b * 100.0 / total))
    return ','.join(values)


def part(cuts, now):
    """the chapter (from 1) that the time is in"""
    return 1 + sum(1 for cut in cuts if now >= cut)


def same_file(a, b):
    """the snapshot's path and the playing file: the same, also when one is URL-quoted"""
    if not a or not b:
        return False
    if a == b:
        return True
    a, b = unquote(a), unquote(b)
    return a == b or a.replace('\\', '/').rsplit('/', 1)[-1] == b.replace('\\', '/').rsplit('/', 1)[-1]


def parse(raw, playing):
    """the segments of the snapshot when it belongs to the playing file, else []"""
    try:
        data = json.loads(raw) if raw else {}
    except ValueError:
        return []
    if not isinstance(data, dict) or data.get('v') != 1 or not same_file(data.get('path'), playing):
        return []
    segments = data.get('segments')
    return segments if isinstance(segments, list) else []


class SkippyChapters(object):
    """the service's tick: reads the snapshot when it or the file changes, the time every tick"""

    def __init__(self):
        self.key = None
        self.cuts = []
        self.total = 0.0
        self.shown = {}

    def _set(self, home, key, value):
        if self.shown.get(key, '') != value:
            home.setProperty(key, value)
            self.shown[key] = value

    def tick(self):
        import xbmc
        import xbmcgui
        home = xbmcgui.Window(10000)
        player = xbmc.Player()
        if not player.isPlayingVideo():
            if self.key is not None or any(self.shown.values()):
                self.key, self.cuts, self.total = None, [], 0.0
                for key in KEYS:
                    self._set(home, key, '')
            return
        try:
            playing = player.getPlayingFile()
            raw = home.getProperty(SNAP)
            key = (raw, playing)
            if key != self.key or (raw and self.total <= 0):
                self.key = key
                self.total = float(player.getTotalTime() or 0)
                self.cuts = boundaries(parse(raw, playing), self.total)
            now = player.getTime() if self.cuts else 0
        except Exception:                # the player stopped between two calls
            return
        self._set(home, 'aeon.sk.ranges', ranges(self.cuts, self.total))
        self._set(home, 'aeon.sk.count', str(len(self.cuts) + 1) if self.cuts else '')
        self._set(home, 'aeon.sk.part', str(part(self.cuts, now)) if self.cuts else '')
