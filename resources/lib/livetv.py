# -*- coding: utf-8 -*-
"""0.3.123 - Live TV in the Fused Glass style (skin 0.56.53, canvas round 8).

Guide days (Days.tick while the TV guide is open): eight chips from today (aeon.gd.dN, N = 1..8: "Today · Fri 20",
"Sat 21" ..., a gold dot where a timer is set), which day the focused programme is on (aeon.gd.cur) and that day in
words for the programme's time line (aeon.gd.long, "Friday 20 November"). The focused programme is read through
guiread (Kodi's main thread); Kodi writes ListItem.StartDate in the region's short date.
Timer rules (rules_list): the TV timer rules as items for the skin's rule cards - title, a sentence of what the rule
catches (when, which days, which channel, by words), channel logo; RunScript(script.aeon.helper,livetv,delrule)
deletes the rule of the focused row after asking."""
import calendar
import datetime
import json
import time

import xbmc
import xbmcgui

HOME = 10000


def home():
    return xbmcgui.Window(HOME)


def rpc(method, params=None):
    return json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}}))).get('result') or {}


def local(utc):
    try:
        return datetime.datetime.fromtimestamp(calendar.timegm(time.strptime(utc, '%Y-%m-%d %H:%M:%S')))
    except (ValueError, TypeError):
        return None


def short_day(d, today):
    if d == today:
        return '%s · %s %d' % (xbmc.getLocalizedString(33006), xbmc.getLocalizedString(41 + d.weekday()), d.day)
    return '%s %d' % (xbmc.getLocalizedString(41 + d.weekday()), d.day)


def long_day(d):
    """'Friday 20 November' from Kodi's own day and month names"""
    return '%s %d %s' % (xbmc.getLocalizedString(11 + d.weekday()), d.day, xbmc.getLocalizedString(21 + d.month - 1))


def parse_kodi_date(label):
    fmt = xbmc.getRegion('dateshort') or '%d-%m-%Y'
    for f in (fmt, fmt.replace('%Y', '%y'), '%d-%m-%Y', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.datetime.strptime(label.strip(), f).date()
        except (ValueError, AttributeError):
            continue
    return None


class Days(object):
    def __init__(self):
        self.on = False
        self.last = 0
        self.props = {}

    def put(self, key, value):
        if self.props.get(key) != value:
            self.props[key] = value
            home().setProperty(key, value)

    def tick(self):
        if not xbmc.getCondVisibility('Window.IsActive(tvguide)'):
            self.on = False
            return
        today = datetime.date.today()
        if not self.on or time.time() - self.last > 30:
            self.on, self.last = True, time.time()
            marked = set()
            for t in rpc('PVR.GetTimers', {'properties': ['starttime', 'istimerrule']}).get('timers') or []:
                s = local(t.get('starttime'))
                if s and not t.get('istimerrule'):
                    marked.add(s.date())
            for n in range(8):
                d = today + datetime.timedelta(days=n)
                self.put('aeon.gd.d%d' % (n + 1), short_day(d, today) + ('  [COLOR fg_mark]•[/COLOR]' if d in marked else ''))
        label = xbmc.getInfoLabel('Container(50).ListItem.StartDate')
        d = parse_kodi_date(label)
        if d is None:                       # long dates ('Friday, 20 November 2026'): the day number picks the chip
            import re
            nums = [int(x) for x in re.findall(r'\d+', label or '') if 1 <= int(x) <= 31]
            d = next((today + datetime.timedelta(days=k) for k in range(8) if nums and (today + datetime.timedelta(days=k)).day == nums[0]), None)
        n = (d - today).days if d else -1
        self.put('aeon.gd.cur', str(n + 1) if 0 <= n < 8 else '')
        self.put('aeon.gd.long', long_day(d) if d else '')
        for key, value in now_pill(xbmc.getInfoLabel('System.Time')).items():
            self.put(key, value)


def now_pill(clock):
    """0.3.128 (skin 0.56.56, Fusion guide: "add small current time pill above the yellow dot"): the guide's ruler has
    one item per half hour, labelled like System.Time ("16:30", "4:30 PM"). aeon.gd.half is the label of the half hour
    now runs in and aeon.gd.min the minutes into it (0..29), so the ruler item with that label draws the pill at that
    minute's place - it follows the grid when it scrolls. aeon.gd.hidelbl names the ruler label the pill would cover
    (this half's own label early on, the next one late in the half)."""
    import re
    m = re.search(r'(\d{1,2}):(\d{2})', clock or '')
    if not m:
        return {'aeon.gd.half': '', 'aeon.gd.min': '', 'aeon.gd.hidelbl': ''}
    hour, mins = m.group(1), int(m.group(2))
    half = '00' if mins < 30 else '30'
    twelve = bool(re.search(r'[^\d\s:]', clock[m.end():] + clock[:m.start()]))

    def label(h, mm):
        return clock[:m.start()] + h + ':' + mm + clock[m.end():]
    hide = ''
    if mins % 30 < 8:
        hide = label(hour, half)
    elif mins % 30 >= 22:
        if half == '00':
            hide = label(hour, '30')
        else:
            h = int(hour) + 1
            if not twelve:
                hide = label(str(h % 24).zfill(len(hour)), '00')
            elif h != 12:                    # (11:30 -> 12:00 flips AM / PM, the region's own word: left alone)
                hide = label(str(1 if h == 13 else h).zfill(2 if hour.startswith('0') else 1), '00')
    return {'aeon.gd.half': label(hour, half), 'aeon.gd.min': str(mins % 30), 'aeon.gd.hidelbl': hide}


WEEK = (11, 12, 13, 14, 15, 16, 17)          # Kodi: Monday .. Sunday


def sentence(t, channel):
    """what a rule catches, in Kodi's own words where it has them"""
    parts = []
    if t.get('epgsearchstring'):
        parts.append('"%s"' % t['epgsearchstring'])
    days = t.get('weekdays') or []
    if days:
        order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        idx = sorted({order.index(d.lower()) if isinstance(d, str) and d.lower() in order else (int(d) - 1 if str(d).isdigit() else -1)
                      for d in (days if isinstance(days, list) else [])} - {-1})
        names = [xbmc.getLocalizedString(WEEK[i]) for i in idx if 0 <= i < 7]
        if len(days) == 7:
            parts.append(xbmc.getLocalizedString(808) or 'Every day')
        elif names:
            parts.append(', '.join(names))
    s = local(t.get('starttime'))
    if s and not t.get('startanytime'):
        parts.append(s.strftime('%H:%M'))
    if channel:
        parts.append(channel)
    if t.get('isreminder'):
        parts.append(xbmc.getLocalizedString(19215) or 'Reminders')
    return '  ·  '.join(parts)


def rules_list():
    chans = {}
    for c in rpc('PVR.GetChannels', {'channelgroupid': 'alltv', 'properties': ['icon']}).get('channels') or []:
        chans[c.get('channelid')] = (c.get('label', ''), c.get('icon', ''))
    props = ['title', 'starttime', 'endtime', 'channelid', 'isreminder', 'istimerrule', 'state', 'weekdays', 'epgsearchstring', 'isradio']
    out = []
    for t in rpc('PVR.GetTimers', {'properties': props}).get('timers') or []:
        if not t.get('istimerrule') or t.get('isradio'):
            continue
        name, icon = chans.get(t.get('channelid'), ('', ''))
        item = xbmcgui.ListItem(label=t.get('title') or '', label2=sentence(t, name), offscreen=True)
        item.setArt({'icon': icon, 'thumb': icon})
        item.setProperty('timerid', str(t.get('timerid')))
        item.setProperty('off', '1' if str(t.get('state') or '').lower() == 'disabled' else '')
        out.append(('plugin://script.aeon.helper/?info=noop', item, False))
    return out


def delete_rule():
    w = home()
    title = xbmc.getInfoLabel('Container(50).ListItem.Label')
    for t in rpc('PVR.GetTimers', {'properties': ['title', 'istimerrule']}).get('timers') or []:
        if t.get('istimerrule') and t.get('title') == title:
            if xbmcgui.Dialog().yesno(xbmc.getLocalizedString(19060), title):
                rpc('PVR.DeleteTimer', {'timerid': t.get('timerid')})
                w.setProperty('aeon.tr.stamp', str(time.time()))
            return
