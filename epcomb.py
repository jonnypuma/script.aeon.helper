# -*- coding: utf-8 -*-
"""The Fused Glass library view Episode combined (skin 0.44.0, helper 0.3.75).

plugin://script.aeon.helper/?info=seasons&path=<Container.FolderPath>  (path last: it may hold & and ?)
    the seasons of the show of an episode list, for the view's season pills: label "Season 3", label2 the number of
    episodes, aeon.ec.done = 1 when every episode is watched, aeon.ec.here = 1 for the season on screen. As it runs it
    sets Window(Home) aeon.ec.stats ("1 in progress · 3 unwatched" / "All watched") and aeon.ec.next ("S3 E5 airs
    Wednesday 18 November") for the season on screen.
publish_focus(dbtype, dbid): the service, when the episode in focus of list 538 changes: aeon.ec.left ("38 min left")
    and aeon.ec.resume ("35:44 of 73:34 · 38 min left"), empty for an episode not started."""
import datetime
import json
import re

import xbmc
import xbmcaddon
import xbmcgui

import nextaired
from resources.lib import favspot

PATH = re.compile(r'videodb://[a-z]+/(?:titles/)?(\d+)/(-?\d+)/?(?:[?#]|$)')


def rpc(method, params):
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return json.loads(xbmc.executeJSONRPC(request)).get('result') or {}


def text(ident, default):
    try:
        return xbmcaddon.Addon('skin.aeon.fuse').getLocalizedString(ident) or default
    except Exception:
        return default


def show_season(path):
    """videodb://tvshows/titles/2301/3/ -> (2301, 3); (0, None) when the path is not one season of one show."""
    found = PATH.search(path or '')
    return (int(found.group(1)), int(found.group(2))) if found else (0, None)


def clock(seconds):
    seconds = int(seconds or 0)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return '%d:%02d:%02d' % (hours, minutes, secs) if hours else '%d:%02d' % (minutes, secs)


def seasons(path):
    """(path, ListItem, isfolder) for the season pills."""
    home = xbmcgui.Window(10000)
    showid, here = show_season(path)
    if not showid:
        home.clearProperty('aeon.ec.stats')
        home.clearProperty('aeon.ec.next')
        return []
    found = rpc('VideoLibrary.GetSeasons', {'tvshowid': showid, 'properties': ['season', 'episode', 'watchedepisodes']}).get('seasons') or []
    word = xbmc.getLocalizedString(20373)
    items = []
    for season in sorted(found, key=lambda s: (s.get('season', 0) == 0, s.get('season', 0))):
        number = season.get('season', 0)
        label = xbmc.getLocalizedString(20381) if number == 0 else '%s %d' % (word, number)
        item = xbmcgui.ListItem(label, str(season.get('episode') or 0), offscreen=True)
        if season.get('episode') and season.get('watchedepisodes', 0) >= season.get('episode'):
            item.setProperty('aeon.ec.done', '1')
        if number == here:
            item.setProperty('aeon.ec.here', '1')
        items.append(('videodb://tvshows/titles/%d/%d/' % (showid, number), item, True))
    # the season on screen: how far you are, and the next airing of the show
    episodes = rpc('VideoLibrary.GetEpisodes', {'tvshowid': showid, 'season': here, 'properties': ['playcount', 'resume']}).get('episodes') or []
    started = sum(1 for e in episodes if not e.get('playcount') and ((e.get('resume') or {}).get('position') or 0) > 0)
    fresh = sum(1 for e in episodes if not e.get('playcount') and not ((e.get('resume') or {}).get('position') or 0) > 0)
    parts = []
    if started:
        parts.append(favspot.fill(text(32541, '{n} in progress'), n=started))
    if fresh:
        parts.append(favspot.fill(text(32542, '{n} unwatched'), n=fresh))
    home.setProperty('aeon.ec.stats', u' · '.join(parts) if parts else (text(32543, 'All watched') if episodes else ''))
    title = (rpc('VideoLibrary.GetTVShowDetails', {'tvshowid': showid, 'properties': ['title']}).get('tvshowdetails') or {}).get('title')
    today = datetime.date.today()
    airing = favspot.next_airing(nextaired.kept('episodes'), title, today)
    nxt = ''
    if airing:
        date = favspot.air_date(airing.get('premiered'), today, [xbmc.getLocalizedString(n) for n in range(11, 18)],
                                [xbmc.getLocalizedString(n) for n in range(21, 33)],
                                {'today': xbmc.getLocalizedString(33006), 'tomorrow': xbmc.getLocalizedString(33007)})
        nxt = favspot.fill(text(32513, '{episode} airs {date}'), episode=favspot.episode_tag(airing.get('season'), airing.get('episode')), date=date)
    home.setProperty('aeon.ec.next', nxt)
    return items


def publish_focus(dbtype, dbid):
    home = xbmcgui.Window(10000)
    left = resume = ''
    if dbtype == 'episode' and str(dbid).isdigit():
        details = rpc('VideoLibrary.GetEpisodeDetails', {'episodeid': int(dbid), 'properties': ['resume', 'runtime']}).get('episodedetails') or {}
        position = float((details.get('resume') or {}).get('position') or 0)
        total = float((details.get('resume') or {}).get('total') or 0) or float(details.get('runtime') or 0)
        if position > 0 and total:
            _pct, minutes = favspot.progress(details)
            left = favspot.fill(text(32512, '{n} min left'), n=minutes)
            resume = '%s  ·  %s' % (favspot.fill(text(32546, '{time} of {total}'), time=clock(position), total=clock(total)), left)
    home.setProperty('aeon.ec.left', left)
    home.setProperty('aeon.ec.resume', resume)


_SHOW_OF = {}


def publish_season(dbtype, dbid):
    """0.3.115: for a season in focus (Fused Glass season views, skin 0.56.53) the next airing of its show:
    aeon.sn.next ("S3 E7 airs Wednesday 25 November"), aeon.sn.dbid the season it belongs to; both empty otherwise."""
    home = xbmcgui.Window(10000)
    nxt = ''
    if dbtype == 'season' and str(dbid).isdigit():
        seasonid = int(dbid)
        if seasonid not in _SHOW_OF:
            details = rpc('VideoLibrary.GetSeasonDetails', {'seasonid': seasonid, 'properties': ['tvshowid', 'showtitle']}).get('seasondetails') or {}
            _SHOW_OF[seasonid] = details.get('showtitle') or ''
        title = _SHOW_OF[seasonid]
        today = datetime.date.today()
        airing = favspot.next_airing(nextaired.kept('episodes'), title, today) if title else None
        if airing:
            date = favspot.air_date(airing.get('premiered'), today, [xbmc.getLocalizedString(n) for n in range(11, 18)],
                                    [xbmc.getLocalizedString(n) for n in range(21, 33)],
                                    {'today': xbmc.getLocalizedString(33006), 'tomorrow': xbmc.getLocalizedString(33007)})
            nxt = favspot.fill(text(32513, '{episode} airs {date}'), episode=favspot.episode_tag(airing.get('season'), airing.get('episode')), date=date)
    home.setProperty('aeon.sn.next', nxt)
    home.setProperty('aeon.sn.dbid', str(dbid) if nxt else '')
