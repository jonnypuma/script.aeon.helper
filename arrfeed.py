# -*- coding: utf-8 -*-
"""Planner sources: wanted titles from Radarr, Sonarr and Lidarr (skin 0.33.0).

The addresses and API keys are the add-on's settings (Planner sources); the key is sent in the X-Api-Key header to the
address you enter, nowhere else, and is never put in a picture address. Each app's calendar is read every three hours
while nothing plays (and at once with Read now in the settings); the result is kept in addon_data/.../arr.json. A
source that cannot be reached keeps what it gave last time. resources/lib/arr.py turns the answers into Planner
entries; nextaired.kept() adds them to the Planner's own list."""
import datetime
import json
import os
import time

try:
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen
except ImportError:                      # pragma: no cover
    from urllib import urlencode
    from urllib2 import Request, urlopen

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib import arr

SOURCES = (('radarr', '/api/v3/calendar', {'unmonitored': 'false'}),
           ('sonarr', '/api/v3/calendar', {'unmonitored': 'false', 'includeSeries': 'true'}),
           ('lidarr', '/api/v1/calendar', {'unmonitored': 'false', 'includeArtist': 'true'}))
EVERY = 3 * 3600
NAMES = {'radarr': 'Radarr', 'sonarr': 'Sonarr', 'lidarr': 'Lidarr'}


def addon():
    return xbmcaddon.Addon('script.aeon.helper')


def path():
    folder = xbmcvfs.translatePath('special://profile/addon_data/script.aeon.helper/')
    if not os.path.isdir(folder):
        os.makedirs(folder)
    return os.path.join(folder, 'arr.json')


def read():
    try:
        with open(path(), 'r', encoding='utf-8') as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def entries():
    """All wanted entries kept (every source)."""
    data = read()
    found = []
    for name, _, _ in SOURCES:
        found.extend((data.get(name) or {}).get('entries') or [])
    return found


def stamp():
    try:
        return os.path.getmtime(path())
    except OSError:
        return 0


def configured():
    settings = addon()
    return [(name, settings.getSetting('%s_url' % name).strip(), settings.getSetting('%s_key' % name).strip())
            for name, _, _ in SOURCES if settings.getSetting('%s_url' % name).strip() and settings.getSetting('%s_key' % name).strip()]


def base_url(url):
    url = url.strip().rstrip('/')
    return url if url.startswith('http://') or url.startswith('https://') else 'http://' + url


def call(url, key, api, params):
    request = Request('%s%s?%s' % (base_url(url), api, urlencode(params)),
                      headers={'X-Api-Key': key, 'Accept': 'application/json', 'User-Agent': 'Kodi'})
    with urlopen(request, timeout=20) as answer:
        return json.loads(answer.read().decode('utf-8'))


def days_ahead():
    try:
        return max(7, min(365, int(addon().getSetting('arr_days') or 60)))
    except ValueError:
        return 60


def library_shows():
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'VideoLibrary.GetTVShows', 'params': {'properties': ['title']}})
    shows = (json.loads(xbmc.executeJSONRPC(request)).get('result') or {}).get('tvshows') or []
    return [show.get('title') or '' for show in shows]


def refresh():
    """Read every configured source; returns {source: count or None (could not be reached)}."""
    today = datetime.date.today()
    days = days_ahead()
    data = read()
    result = {}
    shows = None
    wanted = dict((name, (url, key)) for name, url, key in configured())
    for name, api, extra in SOURCES:
        if name not in wanted:
            data.pop(name, None)                      # switched off: forget what it gave
            continue
        url, key = wanted[name]
        first = today - datetime.timedelta(days=arr.NOW_DAYS) if name == 'radarr' else today
        params = dict(extra, start=first.isoformat(), end=(today + datetime.timedelta(days=days)).isoformat())
        try:
            answer = call(url, key, api, params)
        except Exception as error:                    # wrong address or key, the app is down: keep the old entries
            xbmc.log('[script.aeon.helper] Planner source %s: %s' % (name, error), xbmc.LOGWARNING)
            result[name] = None
            continue
        if name == 'radarr':
            found = arr.radarr_entries(answer, today, days)
        elif name == 'sonarr':
            shows = library_shows() if shows is None else shows
            found = arr.sonarr_entries(answer, today, days, shows)
        else:
            found = arr.lidarr_entries(answer, today, days)
        data[name] = {'time': time.time(), 'entries': found}
        result[name] = len(found)
    data['time'] = time.time()
    target = path()
    with open(target + '.tmp', 'w', encoding='utf-8') as handle:
        json.dump(data, handle)
    os.replace(target + '.tmp', target)
    xbmc.log('[script.aeon.helper] Planner sources: %s' % result, xbmc.LOGINFO)
    xbmcgui.Window(10000).setProperty('aeon.arr.summary', summary(result))
    return result


def summary(result):
    words = addon().getLocalizedString
    parts = []
    for name, _, _ in SOURCES:
        if name in result:
            parts.append('%s %s' % (NAMES[name], result[name] if result[name] is not None else words(32044)))
    return '  ·  '.join(parts)


def tick(state, playing):
    """From the service loop: read every three hours while nothing plays (the first read a minute after start)."""
    now = time.time()
    if 'arrnext' not in state:
        state['arrnext'] = now + 60
        kept = read()                                  # what the last read gave, for the Planner's options row
        found = dict((name, len((kept.get(name) or {}).get('entries') or [])) for name, _, _ in SOURCES if name in kept)
        xbmcgui.Window(10000).setProperty('aeon.arr.summary', summary(found) if found else '')
    if now < state['arrnext'] or playing or state.get('arrbusy'):
        return
    state['arrnext'] = now + EVERY
    if not configured():
        return
    import threading

    def run():
        state['arrbusy'] = True
        try:
            refresh()
        finally:
            state['arrbusy'] = False
    threading.Thread(target=run).start()


def main():
    """Read now (the setting's button): read at once and say what came back."""
    if not configured():
        xbmcgui.Dialog().notification(addon().getLocalizedString(32030), addon().getLocalizedString(32045), xbmcgui.NOTIFICATION_INFO, 5000)
        return
    result = refresh()
    xbmcgui.Dialog().notification(addon().getLocalizedString(32030), summary(result), xbmcgui.NOTIFICATION_INFO, 6000)
