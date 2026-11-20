# -*- coding: utf-8 -*-
"""The Fused Glass Search window (skin 0.42.0, helper 0.3.73).

The window has its own keyboard: letter and digit keys add to Window(Home).Property(aeon.q) in the skin itself;
RunScript(script.aeon.helper,searchkey,del|space|clear|kodi) does the rest (kodi = Kodi's own keyboard, for any text).
The rows beside the keyboard are the library's own paths, so OK, resume and context menus work as in the library.
For the show in focus the service publishes aeon.show.on ("You're on S3 E1") and aeon.show.next ("S3 E5 airs
Wednesday 18 November"). plugin ?info=searchlib lists library shows / films for Home > Search and for People."""
import datetime
import json

import xbmc
import xbmcaddon
import xbmcgui

import nextaired
from resources.lib import favspot

Q = 'aeon.q'
SKIN = 'skin.aeon.fuse'


def rpc(method, params):
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return json.loads(xbmc.executeJSONRPC(request)).get('result') or {}


def text(ident, default):
    try:
        return xbmcaddon.Addon(SKIN).getLocalizedString(ident) or default
    except Exception:
        return default


def key(arg):
    """searchkey,del / space / clear / kodi."""
    home = xbmcgui.Window(10000)
    query = home.getProperty(Q)
    if arg == 'del':
        query = query[:-1]
    elif arg == 'space':
        query = query + ' ' if query and not query.endswith(' ') else query
    elif arg == 'clear':
        query = ''
    elif arg == 'kodi':
        board = xbmc.Keyboard(query, xbmc.getLocalizedString(137))
        board.doModal()
        if not board.isConfirmed():
            return
        query = board.getText().strip()
    home.setProperty(Q, query)


def show_state(tvshowid):
    """("You're on S3 E1", "S3 E5 airs Wednesday 18 November") for a library show; '' where there is nothing."""
    episodes = rpc('VideoLibrary.GetEpisodes', {'tvshowid': tvshowid, 'properties': ['season', 'episode', 'playcount', 'resume',
                                                                                    'lastplayed']}).get('episodes') or []
    chosen, _started, _more = favspot.continue_episode(episodes)
    on = favspot.fill(text(32518, "You're on {episode}"), episode=favspot.episode_tag(chosen.get('season'), chosen.get('episode'))) if chosen else ''
    title = (rpc('VideoLibrary.GetTVShowDetails', {'tvshowid': tvshowid, 'properties': ['title']}).get('tvshowdetails') or {}).get('title')
    today = datetime.date.today()
    airing = favspot.next_airing(nextaired.kept('episodes'), title, today)
    nxt = ''
    if airing:
        date = favspot.air_date(airing.get('premiered'), today, [xbmc.getLocalizedString(n) for n in range(11, 18)],
                                [xbmc.getLocalizedString(n) for n in range(21, 33)],
                                {'today': xbmc.getLocalizedString(33006), 'tomorrow': xbmc.getLocalizedString(33007)})
        nxt = favspot.fill(text(32513, '{episode} airs {date}'), episode=favspot.episode_tag(airing.get('season'), airing.get('episode')), date=date)
    return on, nxt


def publish_show(dbtype, dbid):
    """Called by the service when the focused item changes: only the Search window's show card uses it."""
    on = nxt = ''
    if dbtype == 'tvshow' and str(dbid).isdigit() and xbmc.getCondVisibility('Window.IsActive(1150) + Skin.HasSetting(aeon.fglass)'):
        try:
            on, nxt = show_state(int(dbid))
        except Exception as error:
            xbmc.log('[script.aeon.helper] search show state: %s' % error, xbmc.LOGINFO)
    home = xbmcgui.Window(10000)
    home.setProperty('aeon.show.on', on)
    home.setProperty('aeon.show.next', nxt)


def library_items(kind, query, limit=30):
    """Library shows / films whose title (kind all, tvshow, movie) or cast (kind people) holds the query, as
    (path, ListItem, isfolder) for a plugin directory: shows first, then films."""
    query = (query or '').strip()
    if not query:
        return []
    field = 'actor' if kind == 'people' else 'title'
    rule = {'field': field, 'operator': 'contains', 'value': query}
    items = []
    if kind in ('all', 'tvshow', 'people'):
        shows = rpc('VideoLibrary.GetTVShows', {'filter': rule, 'properties': ['title', 'art', 'year', 'plot', 'studio', 'genre'],
                                                'sort': {'method': 'sorttitle'}, 'limits': {'end': limit}}).get('tvshows') or []
        for show in shows:
            item = xbmcgui.ListItem(show.get('title') or show.get('label') or '', xbmc.getLocalizedString(20364), offscreen=True)
            item.setArt(show.get('art') or {})
            tag = item.getVideoInfoTag()
            tag.setDbId(show['tvshowid'])
            tag.setMediaType('tvshow')
            tag.setYear(int(show.get('year') or 0))
            tag.setPlot(show.get('plot') or '')
            items.append(('videodb://tvshows/titles/%d/' % show['tvshowid'], item, True))
    if kind in ('all', 'movie', 'people'):
        films = rpc('VideoLibrary.GetMovies', {'filter': rule, 'properties': ['title', 'art', 'year', 'plot', 'resume', 'runtime', 'file'],
                                               'sort': {'method': 'sorttitle'}, 'limits': {'end': limit}}).get('movies') or []
        for film in films:
            item = xbmcgui.ListItem(film.get('title') or film.get('label') or '', xbmc.getLocalizedString(20338), offscreen=True)
            item.setArt(film.get('art') or {})
            tag = item.getVideoInfoTag()
            tag.setDbId(film['movieid'])
            tag.setMediaType('movie')
            tag.setYear(int(film.get('year') or 0))
            tag.setPlot(film.get('plot') or '')
            resume = film.get('resume') or {}
            if resume.get('position'):
                tag.setResumePoint(float(resume['position']), float(resume.get('total') or film.get('runtime') or 0))
            item.setProperty('IsPlayable', 'true')
            items.append(('videodb://movies/titles/%d' % film['movieid'], item, False))
    return items
