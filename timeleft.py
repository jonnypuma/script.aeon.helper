# -*- coding: utf-8 -*-
""""x min left" on every list row of a film, episode or music video in progress (skin 0.56.8, the list row rule).

Kodi gives a list row its percent played and length but no time left, and the skin cannot do sums. So the service
keeps the time left of every item in progress in Window(Home) properties, one slot each:
    aeon.left.<k>.type  movie / episode / musicvideo
    aeon.left.<k>.id    its library id
    aeon.left.<k>.text  "16 min left" (skin string 32512, as Episode combined says it)
    aeon.left.<k>.hmb   "[B]0[/B]·16 left" (0.3.114: the rows, like the run time beside them)
    aeon.left.<k>.hhmm  "0:16 left" (skin string 32606, after ENDS in the Aeon info bands)
for k = 1..SLOTS, the most recently played first; the skin's FG_L_RowRight shows the slot whose type and id match the
row, else the run time. Refreshed at start, when playback stops and when the video library changes (at most once a
second)."""
import json
import time

import xbmc
import xbmcaddon
import xbmcgui

from resources.lib import favspot

SLOTS = 40
KINDS = (('movie', 'VideoLibrary.GetMovies', 'movies', 'movieid'),
         ('episode', 'VideoLibrary.GetEpisodes', 'episodes', 'episodeid'),
         ('musicvideo', 'VideoLibrary.GetMusicVideos', 'musicvideos', 'musicvideoid'))


def rpc(method, params):
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return json.loads(xbmc.executeJSONRPC(request)).get('result') or {}


def word(sid=32512, default='{n} min left'):
    try:
        return xbmcaddon.Addon('skin.aeon.fuse').getLocalizedString(sid) or default
    except Exception:
        return default


def collect():
    """[(lastplayed, type, id, minutes left)] of everything in progress"""
    found = []
    for kind, method, key, idkey in KINDS:
        result = rpc(method, {'filter': {'field': 'inprogress', 'operator': 'true', 'value': ''},
                              'properties': ['resume', 'runtime', 'lastplayed'],
                              'sort': {'method': 'lastplayed', 'order': 'descending'}, 'limits': {'start': 0, 'end': SLOTS}})
        for item in result.get(key) or []:
            pct, minutes = favspot.progress(item)
            if pct > 0:
                found.append((item.get('lastplayed') or '', kind, item.get(idkey), max(1, minutes)))
    found.sort(reverse=True)
    return found[:SLOTS]


class TimeLeft(object):
    def __init__(self):
        self.due = 0.0            # refresh when time passes this (0 = now)
        self.shown = {}

    def wake(self):
        """after playback stopped or the library changed"""
        self.due = min(self.due, time.time() + 1.0) if self.due else time.time() + 1.0

    def tick(self):
        if self.due is None or time.time() < self.due:
            return
        self.due = None
        try:
            items = collect()
        except Exception as error:               # never stop the service over this
            xbmc.log('[script.aeon.helper] time left: %s' % error, xbmc.LOGINFO)
            return
        home = xbmcgui.Window(10000)
        text = word()
        text_hm = word(32606, '{t} left')
        values = {}
        for k in range(1, SLOTS + 1):
            if k <= len(items):
                _when, kind, dbid, minutes = items[k - 1]
                # 0.3.94: .hm = the time left as the Aeon run-time column writes a run time ("0·07", "1·12")
                values.update({'aeon.left.%d.type' % k: kind, 'aeon.left.%d.id' % k: str(dbid),
                               'aeon.left.%d.text' % k: favspot.fill(text, n=minutes),
                               'aeon.left.%d.hm' % k: u'%d·%02d' % (int(minutes) // 60, int(minutes) % 60),
                               # 0.3.114: .hmb = the time left like the run time beside it, bold hour ("[B]3[/B]·29 left")
                               'aeon.left.%d.hmb' % k: favspot.fill(text_hm, t=u'[B]%d[/B]·%02d' % (int(minutes) // 60, int(minutes) % 60)),
                               # 0.3.95: .hhmm = "0:07 left", after ENDS in the Aeon info bands (skin string 32606)
                               'aeon.left.%d.hhmm' % k: favspot.fill(text_hm, t=u'%d:%02d' % (int(minutes) // 60, int(minutes) % 60))})
            else:
                values.update({'aeon.left.%d.type' % k: '', 'aeon.left.%d.id' % k: '', 'aeon.left.%d.text' % k: '',
                               'aeon.left.%d.hmb' % k: '',
                               'aeon.left.%d.hm' % k: '', 'aeon.left.%d.hhmm' % k: ''})
        for name, value in values.items():
            if self.shown.get(name) != value:
                self.shown[name] = value
                home.setProperty(name, value)
