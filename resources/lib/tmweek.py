# -*- coding: utf-8 -*-
"""0.3.122 - TV Timers as the week in lanes of time (skin 0.56.53, Fused Glass style, canvas round 7 idea B).

While TV Timers is open the service publishes the next five days: a lane per day (aeon.tm.dN.w / .n, N = 1..5, 1 =
today) with up to three timers each (aeon.tm.dNbM.t title, .s "21:00 · channel", .k rec / series / remind, .x start
as 0-99 % of the span, .w width as one of WIDTHS, .off "1" when disabled), the span's hour labels (aeon.tm.h1-7), the
"now" mark (aeon.tm.now, 0-99 or empty), the header (aeon.tm.count, aeon.tm.next, aeon.tm.rec) and which block the
focused row of Kodi's list (50) is (aeon.tm.focus = dNbM, aeon.tm.foff). Hide disabled: aeon.tm.hide.
The list is read through guiread (Kodi's main thread). Script: RunScript(script.aeon.helper,tmweek,delete)."""
import calendar
import datetime
import json
import re
import time

import xbmc
import xbmcgui

DAYS = 5
PER_DAY = 3
WIDTHS = list(range(10, 101, 6))          # block widths in % of the span (the skin draws one variant per width)
HOME = 10000


def home():
    return xbmcgui.Window(HOME)


def rpc(method, params=None):
    return json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}}))).get('result') or {}


def local(utc):
    """Kodi's timer times are UTC 'YYYY-MM-DD HH:MM:SS'"""
    try:
        return datetime.datetime.fromtimestamp(calendar.timegm(time.strptime(utc, '%Y-%m-%d %H:%M:%S')))
    except (ValueError, TypeError):
        return None


def skin(n):
    return xbmc.getInfoLabel('$ADDON[skin.aeon.fuse %d]' % n)


def span_text(mins):
    h, m = divmod(int(mins), 60)
    return ('%d h %02d min' % (h, m)) if h else ('%d min' % m)


def kind(t):
    if t.get('isreminder'):
        return 'remind'
    if t.get('istimerrule') or t.get('weekdays') or t.get('epgsearchstring'):
        return 'series'
    return 'rec'


def hm(label):
    """'21:00' / '9:00 PM' -> (21, 0)"""
    m = re.search(r'(\d{1,2})[:.](\d{2})', label or '')
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    low = (label or '').lower()
    if 'pm' in low and h < 12:
        h += 12
    if 'am' in low and h == 12:
        h = 0
    return h, mi


class Week(object):
    def __init__(self):
        self.on = False
        self.last = 0
        self.slots = {}              # dNbM -> (title, start datetime, timerid, disabled)
        self.props = {}
        self.channels = {}

    def put(self, key, value):
        if self.props.get(key) != value:
            self.props[key] = value
            home().setProperty(key, value)

    def clear(self):
        for key in list(self.props):
            home().clearProperty(key)
        self.props, self.slots, self.on = {}, {}, False

    def channel(self, cid):
        if not self.channels:
            for c in rpc('PVR.GetChannels', {'channelgroupid': 'alltv'}).get('channels') or []:
                self.channels[c.get('channelid')] = c.get('label', '')
        return self.channels.get(cid, '')

    def rebuild(self):
        now = datetime.datetime.now()
        today = now.date()
        hide = bool((rpc('Settings.GetSettingValue', {'setting': 'pvrtimers.hidedisabledtimers'}) or {}).get('value'))
        self.put('aeon.tm.hide', '1' if hide else '')
        props = ['title', 'starttime', 'endtime', 'channelid', 'isreminder', 'istimerrule', 'state', 'weekdays', 'epgsearchstring']   # Kodi 22 has no 'timertype' field
        timers = [t for t in rpc('PVR.GetTimers', {'properties': props}).get('timers') or [] if not t.get('istimerrule')]
        rows = []
        for t in timers:
            s, e = local(t.get('starttime')), local(t.get('endtime'))
            if not s or not e or e < now:
                continue
            off = str(t.get('state') or '').lower() == 'disabled'
            if hide and off:
                continue
            rows.append((s, e, t, off))
        rows.sort(key=lambda r: r[0])
        week = [r for r in rows if 0 <= (r[0].date() - today).days < DAYS]
        # the span: from the earliest start (even hour, at most noon) to midnight
        first = min([r[0].hour for r in week] + [12])
        s0 = max(v for v in (18, 12, 6, 0) if v <= first)          # six equal steps to midnight: 1, 2, 3 or 4 hours
        span = (24 - s0) * 60.0

        def pct(dt):
            return max(0, min(99, int(((dt.hour * 60 + dt.minute) - s0 * 60) / span * 100)))

        for i in range(7):
            self.put('aeon.tm.h%d' % (i + 1), '%02d' % ((s0 + (24 - s0) // 6 * i) % 24))
        nowp = (now.hour * 60 + now.minute) - s0 * 60
        self.put('aeon.tm.now', str(int(nowp / span * 100)) if 0 <= nowp < span else '')
        self.slots = {}
        for d in range(DAYS):
            day = today + datetime.timedelta(days=d)
            self.put('aeon.tm.d%d.w' % (d + 1), xbmc.getLocalizedString(33006) if d == 0 else xbmc.getLocalizedString(41 + day.weekday()))
            self.put('aeon.tm.d%d.n' % (d + 1), str(day.day))
            items = [r for r in week if r[0].date() == day]
            self.put('aeon.tm.d%d.c' % (d + 1), '1' if items else '')
            for b in range(PER_DAY):
                key = 'd%db%d' % (d + 1, b + 1)
                p = 'aeon.tm.%s.' % key
                if b < len(items):
                    s, e, t, off = items[b]
                    mins = max(1, (e - s).seconds // 60) if e.date() == s.date() else (24 * 60 - (s.hour * 60 + s.minute))
                    x = pct(s)
                    room = (pct(items[b + 1][0]) - x) if b + 1 < len(items) else 100 - x   # never into the next block
                    w = max(10, min(mins / span * 100, room))
                    w = max([v for v in WIDTHS if v <= w] or [WIDTHS[0]])   # round down: the block ends before its end
                    if x + w > 100:
                        x = max(0, 100 - w)
                    self.put(p + 't', t.get('title') or '')
                    self.put(p + 's', '%s  ·  %s' % (s.strftime('%H:%M'), self.channel(t.get('channelid'))))
                    self.put(p + 'k', kind(t))
                    self.put(p + 'x', str(int(x)))
                    self.put(p + 'w', str(w))
                    self.put(p + 'off', '1' if off else '')
                    self.slots[key] = (t.get('title') or '', s, t.get('timerid'), off)
                else:
                    for k in ('t', 's', 'k', 'x', 'w', 'off'):
                        self.put(p + k, '')
        self.put('aeon.tm.map', json.dumps({k: [v[0], v[2]] for k, v in self.slots.items()}))
        self.put('aeon.tm.count', str(len(week)))
        if week:
            s, e, t, off = next((r for r in week if r[0] >= now), week[0])
            delta = max(0, int((s - now).total_seconds() // 60))
            self.put('aeon.tm.next', skin(32813).replace('{0}', span_text(delta)) + '  ·  ' + (t.get('title') or ''))
            rec = sum(((r[1] - r[0]).seconds // 60) for r in week if kind(r[2]) != 'remind' and not r[3])
            self.put('aeon.tm.rec', skin(32814).replace('{0}', span_text(rec)) if rec else '')
        else:
            self.put('aeon.tm.next', '')
            self.put('aeon.tm.rec', '')

    def focus(self):
        label = xbmc.getInfoLabel('Container(50).ListItem.Label')
        when = hm(xbmc.getInfoLabel('Container(50).ListItem.StartTime'))
        found = ''
        for key, (title, s, tid, off) in sorted(self.slots.items()):
            if title == label and (when is None or (s.hour, s.minute) == when):
                found = key
                break
        self.put('aeon.tm.focus', found)
        self.put('aeon.tm.foff', '1' if found and self.slots[found][3] else '')

    def tick(self):
        if not xbmc.getCondVisibility('Window.IsActive(tvtimers)'):
            if self.on:
                self.clear()
            return
        stamp = home().getProperty('aeon.tm.refresh')
        if not self.on or time.time() - self.last > 10 or stamp != getattr(self, 'stamp', ''):
            self.stamp = stamp
            self.on, self.last = True, time.time()
            self.put('aeon.tm.on', '1')
            self.rebuild()
        self.focus()

    def refresh(self):
        self.last = 0


def delete():
    """the focused block's timer, after asking"""
    w = home()
    key = w.getProperty('aeon.tm.focus')
    try:
        title, tid = json.loads(w.getProperty('aeon.tm.map') or '{}').get(key) or (None, None)
    except ValueError:
        title, tid = None, None
    if tid is None:
        return
    if xbmcgui.Dialog().yesno(xbmc.getLocalizedString(19060), title or ''):
        rpc('PVR.DeleteTimer', {'timerid': tid})
        w.setProperty('aeon.tm.refresh', str(time.time()))
