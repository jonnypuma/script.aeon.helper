# -*- coding: utf-8 -*-
"""0.3.121 - the Sort and show only panel of the skin (dialog 1179, Fused Glass style): films, TV shows, albums, artists.

Sort: only the sorts Kodi itself offers for each list (others are ignored by Container.SetSortMethod - tested on Kodi
22, 2026-11-20): the row in use is matched by its label (Container.SortMethod is a localized name); OK on it flips the
order. Show only: filters joined with AND into a smart-playlist path (<base>?xsp=...), loaded with Container.Update.
The skin sets Window(Home).Property(aeon.ss.kind) (movies / tvshows / albums / artists) before it opens the panel. The
filters live in Window(Home).Property(aeon.ss.state) and are dropped when the list's path has no xsp.

Properties: aeon.ss.sort (the sort id in use), aeon.ss.total, aeon.ss.n.<key> (how many each filter alone leaves),
aeon.ss.on.<key>, aeon.ss.v.<key> (the picked genres / decade / rating), aeon.ss.chips (the filters in force).
Script: RunScript(script.aeon.helper,sortshow,open|sort,<id>|show,<key>)."""
import json
from urllib.parse import quote

import xbmc
import xbmcgui

KINDS = {
    'movies': {
        'base': 'videodb://movies/titles/', 'type': 'movies', 'method': 'VideoLibrary.GetMovies', 'key': 'movies', 'genres': ('VideoLibrary.GetGenres', 'movie'),
        'sorts': [(29, 556), (16, 562), (40, 570), (9, 180), (17, 563), (18, 38018), (31, 20074), (42, 567), (41, 568)],
        'counted': {
            'unwatched': {'field': 'playcount', 'operator': 'is', 'value': ['0']},
            'inprogress': {'field': 'inprogress', 'operator': 'true', 'value': []},
            'watched': {'field': 'playcount', 'operator': 'greaterthan', 'value': ['0']},
            '4k': {'field': 'videoresolution', 'operator': 'greaterthan', 'value': ['1080']},
            'hdr': {'field': 'hdrtype', 'operator': 'is', 'value': ['dolbyvision', 'hdr10', 'hlg']},
            'versions': {'field': 'hasversions', 'operator': 'true', 'value': []}},
        'picked': ('genre', 'decade', 'mpaa'), 'exclusive': (('unwatched', 'inprogress', 'watched'),)},
    'tvshows': {
        'base': 'videodb://tvshows/titles/', 'type': 'tvshows', 'method': 'VideoLibrary.GetTVShows', 'key': 'tvshows', 'genres': ('VideoLibrary.GetGenres', 'tvshow'),
        'sorts': [(29, 556), (16, 562), (40, 570), (17, 563), (18, 38018), (41, 568), (25, 20360)],
        'counted': {
            'unwatched': {'field': 'playcount', 'operator': 'is', 'value': ['0']},
            'inprogress': {'field': 'inprogress', 'operator': 'true', 'value': []},
            'watched': {'field': 'playcount', 'operator': 'greaterthan', 'value': ['0']},
            'continuing': {'field': 'status', 'operator': 'is', 'value': ['Continuing', 'Returning Series']},
            'ended': {'field': 'status', 'operator': 'is', 'value': ['Ended', 'Canceled', 'Cancelled']}},
        'picked': ('genre', 'decade', 'mpaa'), 'exclusive': (('unwatched', 'inprogress', 'watched'), ('continuing', 'ended'))},
    'albums': {
        'base': 'musicdb://albums/', 'type': 'albums', 'method': 'AudioLibrary.GetAlbums', 'key': 'albums', 'genres': ('AudioLibrary.GetGenres', None),
        'sorts': [(12, 558), (10, 557), (11, 578), (16, 562), (17, 563), (18, 38018), (40, 570), (41, 568), (42, 567)],
        'counted': {
            'neverplayed': {'field': 'playcount', 'operator': 'is', 'value': ['0']},
            'played': {'field': 'playcount', 'operator': 'greaterthan', 'value': ['0']}},
        'picked': ('genre', 'decade'), 'exclusive': (('neverplayed', 'played'),)},
    'artists': {
        'base': 'musicdb://artists/', 'type': 'artists', 'method': 'AudioLibrary.GetArtists', 'key': 'artists', 'genres': ('AudioLibrary.GetGenres', None),
        'sorts': [(10, 557), (40, 570)],
        'counted': {}, 'picked': ('genre',), 'exclusive': ()},
}
NAMES = {'unwatched': 16101, 'inprogress': 575, 'watched': 16102, '4k': None, 'hdr': None, 'versions': 32807,
         'continuing': 32390, 'ended': 32391, 'neverplayed': 32810, 'played': 32811,
         'genre': 515, 'decade': 32808, 'mpaa': 20074}


def home():
    return xbmcgui.Window(10000)


def kind():
    return KINDS.get(home().getProperty('aeon.ss.kind')) or KINDS['movies']


def rpc(method, params):
    return json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}))).get('result') or {}


def total(k, flt=None):
    p = {'limits': {'start': 0, 'end': 1}}
    if flt:
        p['filter'] = flt
    return (rpc(k['method'], p).get('limits') or {}).get('total', 0)


def load():
    if 'xsp=' not in xbmc.getInfoLabel('Container.FolderPath'):
        return {}
    try:
        return json.loads(home().getProperty('aeon.ss.state') or '{}')
    except ValueError:
        return {}


def rules(k, state):
    out = []
    for key, value in state.items():
        if key in k['counted']:
            out.append(k['counted'][key])
        elif key in ('genre', 'mpaa'):
            out.append({'field': key, 'operator': 'is', 'value': value})
        elif key == 'decade':
            d = int(value)
            out.append({'field': 'year', 'operator': 'greaterthan', 'value': [str(d - 1)]})
            out.append({'field': 'year', 'operator': 'lessthan', 'value': [str(d + 10)]})
    return out


def name(key):
    if key == '4k':
        return '4K'
    if key == 'hdr':
        return 'HDR'
    n = NAMES[key]
    return xbmc.getInfoLabel('$ADDON[skin.aeon.fuse %d]' % n) if n >= 32000 else xbmc.getLocalizedString(n)


def value_text(key, value):
    return '%ds' % int(value) if key == 'decade' else ', '.join(value)


def publish(k, state):
    w = home()
    w.setProperty('aeon.ss.state', json.dumps(state))
    for key in list(k['counted']) + list(k['picked']):
        w.setProperty('aeon.ss.on.%s' % key, '1' if key in state else '')
        if key in k['picked']:
            w.setProperty('aeon.ss.v.%s' % key, value_text(key, state[key]) if key in state else '')
    chips = [(value_text(x, v) if x in k['picked'] else name(x)) for x, v in state.items()]
    w.setProperty('aeon.ss.chips', '  ·  '.join(chips))
    now = xbmc.getInfoLabel('Container.SortMethod')
    w.setProperty('aeon.ss.sort', next((str(i) for i, s in k['sorts'] if xbmc.getLocalizedString(s) == now), ''))


def apply(k, state):
    r = rules(k, state)
    url = k['base'] if not r else k['base'] + '?xsp=' + quote(json.dumps({'type': k['type'], 'rules': {'and': r}}))
    xbmc.executebuiltin('Container.Update(%s,replace)' % url)
    publish(k, state)


def pick(k, key, state):
    dialog = xbmcgui.Dialog()
    if key == 'genre':
        method, gtype = k['genres']
        found = rpc(method, {'type': gtype} if gtype else {}).get('genres') or []
        genres = sorted({g['label'] for g in found})
        now = state.get('genre') or []
        chosen = dialog.multiselect(name('genre'), genres, preselect=[genres.index(g) for g in now if g in genres])
        return [genres[i] for i in chosen] if chosen else None
    if key == 'decade':
        years = [m.get('year') or 0 for m in rpc(k['method'], {'properties': ['year']}).get(k['key']) or []]
        decades = sorted({y // 10 * 10 for y in years if y > 1800}, reverse=True)
        i = dialog.select(name('decade'), ['%ds' % d for d in decades])
        return str(decades[i]) if i >= 0 else None
    if key == 'mpaa':
        ratings = sorted({(m.get('mpaa') or '').strip() for m in rpc(k['method'], {'properties': ['mpaa']}).get(k['key']) or []} - {''})
        now = state.get('mpaa') or []
        chosen = dialog.multiselect(name('mpaa'), ratings, preselect=[ratings.index(r) for r in now if r in ratings])
        return [ratings[i] for i in chosen] if chosen else None


def run(argv):
    what = argv[0] if argv else 'open'
    k = kind()
    state = load()
    if what == 'open':
        publish(k, state)                               # the sort in use and the filters first, the counts take a moment
        home().setProperty('aeon.ss.total', str(total(k)))
        for key, rule in k['counted'].items():
            home().setProperty('aeon.ss.n.%s' % key, str(total(k, rule)))
    elif what == 'sort' and len(argv) > 1:
        sid = int(argv[1])
        label = dict(k['sorts']).get(sid)
        if label and xbmc.getInfoLabel('Container.SortMethod') == xbmc.getLocalizedString(label):
            xbmc.executebuiltin('Container.SetSortDirection')
        else:
            xbmc.executebuiltin('Container.SetSortMethod(%d)' % sid)
        xbmc.sleep(300)
        publish(k, state)
    elif what == 'show' and len(argv) > 1:
        key = argv[1]
        if key == 'clear':
            state = {}
        elif key in k['picked']:
            if key in state:
                state.pop(key)
            else:
                value = pick(k, key, state)
                if not value:
                    return
                state[key] = value
        elif key in k['counted']:
            if key in state:
                state.pop(key)
            else:
                state[key] = True
                for group in k['exclusive']:            # watched states, show status: one of each group at a time
                    if key in group:
                        for other in group:
                            if other != key:
                                state.pop(other, None)
        apply(k, state)
