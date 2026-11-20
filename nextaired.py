# -*- coding: utf-8 -*-
"""Upcoming episodes of the shows in the library, for the Planner view.

TMDb Helper's "library: airing next" list asked TMDb about every show of the library (2,142 on the box) in up to 40
threads; on a 4 GB box it ran into TMDb's rate limit and slowed Kodi to a crawl for many minutes. Now only the shows
that can still get episodes (status not Ended / Canceled, about a fifth of them) are asked, one at a time with a
pause, through TMDb Helper's details of each show (its next_aired.* properties; resources/lib/planner.next_episode).
It is still read rarely: every two weeks by default (the Planner's Update option: daily, weekly, every 2 weeks,
monthly), only while Kodi is idle and nothing plays. The list is kept in the add-on's data folder and survives restarts
and crashes: it is written to a new file that then replaces the old one (the old one stays as nextaired.json.bak), and
a read that comes back empty never wipes what was kept (resources/lib/planner.merge)."""
import datetime
import json
import os
import shutil
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import arrfeed
from resources.lib import arr, planner

DETAILS = 'plugin://plugin.video.themoviedb.helper/?info=details&tmdb_type=tv&tmdb_id=%s'
FILMS = 'plugin://plugin.video.themoviedb.helper/?info=upcoming&tmdb_type=movie&page=%d'
EPISODE = DETAILS + '&season=%d&episode=%d'   # 0.3.97: its episode_type (finale / mid_season ...)
FILM_PAGES = 2
STEP = 0.5                            # seconds between two shows
ART = ('thumb', 'still', 'landscape', 'fanart', 'poster', 'clearlogo', 'tvshow.poster', 'tvshow.fanart', 'tvshow.clearlogo', 'tvshow.landscape')


def path():
    folder = xbmcvfs.translatePath('special://profile/addon_data/script.aeon.helper/')
    if not xbmcvfs.exists(folder):
        xbmcvfs.mkdirs(folder)
    return os.path.join(folder, 'nextaired.json')


def rpc(method, params):
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return json.loads(xbmc.executeJSONRPC(request)).get('result') or {}


def _load(name):
    try:
        with open(name, 'r') as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (IOError, OSError, ValueError):
        return None


def read():
    """The kept list; the backup when the file is missing or damaged (a crash while writing, a full disk)."""
    target = path()
    data = _load(target)
    if data is None:
        data = _load(target + '.bak')
    return data or {}


def save(data):
    """Write to a new file, flush it to disk, keep the previous good file as .bak, then swap the new one in."""
    target = path()
    temp = target + '.tmp'
    try:
        with open(temp, 'w') as handle:
            json.dump(data, handle)
            handle.flush()
            os.fsync(handle.fileno())
        if _load(target) is not None:
            shutil.copyfile(target, target + '.bak')
        os.replace(temp, target)
        return True
    except (IOError, OSError) as error:
        xbmc.log('[script.aeon.helper] Planner list not saved: %s' % error, xbmc.LOGWARNING)
        return False


def refresh_setting():
    return planner.refresh_choice(xbmc.getInfoLabel('Skin.String(aeon.planner.refresh)'))


def stale():
    return planner.due(read(), refresh_setting(), time.time())


def kept(what=''):
    """The Planner's list as the 'what' choice says ('' both, 'episodes', 'films'): its own episodes and films plus the
    wanted titles of the Planner sources (Radarr, Sonarr, Lidarr; arrfeed.py), each once."""
    data = read()
    base = []
    if what != 'films':
        base.extend(data.get('episodes') or ())
    if what != 'episodes':
        base.extend(data.get('movies') or ())
    return arr.combine(base, arr.pick(arrfeed.entries(), what))


def upcoming(today=None, days=None, what=''):
    """Kept episodes, films and wanted titles from today on, soonest first. days: only today and that many days ahead.
    what: '' = everything, 'episodes', 'films'."""
    first = today or datetime.date.today()
    last = (first + datetime.timedelta(days=days)).isoformat() if days is not None else '9999'
    found = [entry for entry in kept(what) if first.isoformat() <= (entry.get('premiered') or '') <= last]
    return sorted(found, key=lambda entry: (entry['premiered'], entry.get('showtitle') or entry.get('title') or ''))

def publish_next(state):
    """0.3.94 (skin 0.56.13; the user, on the Aeon Episode list: "next episode airing info if available underneath it"):
    while an episode or season list is open, Window(Home).Property(aeon.next.of) = its show, aeon.next.code = "S3 E5",
    aeon.next.day = "Wed 18 Nov" for the show's soonest episode in the Planner's list (from today on), else empty.
    The file is read only when the show changes."""
    home = xbmcgui.Window(10000)
    show = ''
    if xbmc.getCondVisibility('Window.IsActive(videos) + [Container.Content(episodes) | Container.Content(seasons)]'):
        show = xbmc.getInfoLabel('ListItem.TVShowTitle') or xbmc.getInfoLabel('Container.ShowTitle')
    if show == state.get('nextof'):
        return
    state['nextof'] = show
    code = day = kind = ''
    if show:
        try:
            for entry in upcoming(what='episodes'):
                if entry.get('showtitle') != show:
                    continue
                date = datetime.date.fromisoformat(entry['premiered'][:10])
                code = 'S%s E%s' % (entry.get('season', ''), entry.get('episode', ''))
                day = '%s %d %s' % (xbmc.getLocalizedString(41 + date.weekday()), date.day, xbmc.getLocalizedString(50 + date.month))
                word = planner.EPKIND_WORDS.get(entry.get('epkind') or '')
                kind = xbmcaddon.Addon('script.aeon.helper').getLocalizedString(word) if word else ''
                break
        except Exception as error:                       # a damaged entry: no line rather than a stopped service
            xbmc.log('[script.aeon.helper] next episode: %s' % error, xbmc.LOGINFO)
            code = day = kind = ''
    home.setProperty('aeon.next.of', show if code else '')
    home.setProperty('aeon.next.kind', kind)
    home.setProperty('aeon.next.code', code)
    home.setProperty('aeon.next.day', day)



def publish_season_pct(state):
    """0.3.95 (skin 0.56.15; the user, on the Aeon Compact list: "circle season progress?"): while an episode list is
    open, Window(Home).Property(aeon.cont.pct) = the share of its episodes watched (Kodi's Container.TotalWatched and
    TotalUnWatched; the skin cannot divide) and aeon.cont.path = that list's folder, so the skin shows it only there."""
    home = xbmcgui.Window(10000)
    path = pct = ''
    if xbmc.getCondVisibility('Window.IsActive(videos) + Container.Content(episodes)'):
        path = xbmc.getInfoLabel('Container.FolderPath')
        try:
            watched = int(xbmc.getInfoLabel('Container.TotalWatched') or 0)
            unwatched = int(xbmc.getInfoLabel('Container.TotalUnWatched') or 0)
            if watched + unwatched:
                pct = str(int(round(100.0 * watched / (watched + unwatched))))
        except ValueError:
            pct = ''
    if state.get('contpct') == (path, pct):
        return
    state['contpct'] = (path, pct)
    home.setProperty('aeon.cont.pct', pct)
    home.setProperty('aeon.cont.path', path if pct else '')

def next_type(tmdb, found):
    """TMDb's type of the next episode (series_premiere ... season_finale), from TMDb Helper's details of that episode;
    the first episode of a season needs no question (it is a premiere)"""
    if int(found.get('episode') or 0) == 1 or not found.get('season'):
        return ''
    try:
        files = rpc('Files.GetDirectory', {'directory': EPISODE % (tmdb, int(found['season']), int(found['episode'])), 'media': 'video',
                                           'properties': ['customproperties']}).get('files') or []
        return ((files[0].get('customproperties') or {}).get('episode_type') or '') if files else ''
    except Exception as error:               # no type is only no tag
        xbmc.log('[script.aeon.helper] Planner: episode type: %s' % error, xbmc.LOGDEBUG)
        return ''


def build(monitor=None, step=STEP):
    """Read the list again (the service when it is due, or the Planner's Update now). Never during playback: nothing
    starts while something plays, and a read stops (keeping the old list) as soon as something starts."""
    if not xbmc.getCondVisibility('System.AddonIsEnabled(plugin.video.themoviedb.helper)') or xbmc.Player().isPlaying():
        return None
    episodes = []
    today = datetime.date.today()
    shows = rpc('VideoLibrary.GetTVShows', {'properties': ['title', 'plot', 'status', 'uniqueid']}).get('tvshows') or []
    # an episode nobody has described yet falls back to the plot of its show, which is in the library
    plots = dict((show.get('title') or '', show.get('plot') or '') for show in shows)
    statuses = dict((show.get('title') or '', show.get('status') or '') for show in shows)
    asked = 0
    candidates = planner.airing_candidates(shows)
    xbmc.log('[script.aeon.helper] Planner: reading the next episodes of %d shows' % len(candidates), xbmc.LOGINFO)
    for title, tmdb in candidates:
        files = rpc('Files.GetDirectory', {'directory': DETAILS % tmdb, 'media': 'video',
                                           'properties': ['title', 'art', 'genre', 'rating', 'votes', 'studio', 'mpaa', 'cast',
                                                          'customproperties']}).get('files') or []
        asked += 1
        for entry in files[:1]:
            custom = entry.get('customproperties') or {}
            found = planner.next_episode(title, entry, custom, today)
            if found:
                more = planner.details(entry, custom)
                more['showplot'] = plots.get(title, '')
                found['more'] = more
                found['epkind'] = planner.episode_kind(found['season'], found['episode'], next_type(tmdb, found),
                                                       custom.get('status') or statuses.get(title, ''))
                episodes.append(found)
        if monitor is not None and (monitor.waitForAbort(step) or xbmc.Player().isPlaying()):
            xbmc.log('[script.aeon.helper] Planner: stopped after %d shows, Kodi stops or something plays (the old list is kept)'
                     % asked, xbmc.LOGINFO)
            return None                  # Kodi stops or something plays: keep the old list, try again later
    xbmc.log('[script.aeon.helper] Planner: asked TMDb Helper about %d of %d shows, %d next episodes' % (asked, len(shows), len(episodes)),
             xbmc.LOGINFO)
    movies = []
    listed = set()
    for page in range(1, FILM_PAGES + 1):
        if xbmc.Player().isPlaying():
            return None                  # something started: keep the old list, try again after the next quiet
        files = rpc('Files.GetDirectory', {'directory': FILMS % page, 'media': 'video',
                                           'properties': ['title', 'premiered', 'plot', 'runtime', 'art', 'year', 'genre', 'rating', 'votes', 'studio', 'mpaa', 'cast']}).get('files') or []
        for entry in files:
            title = entry.get('title') or ''
            if entry.get('type') != 'movie' or not entry.get('premiered') or not title or title in listed:
                continue
            listed.add(title)
            art = entry.get('art') or {}
            movies.append({'more': planner.details(entry), 'kind': 'movie', 'title': title, 'premiered': entry['premiered'][:10], 'plot': entry.get('plot') or '',
                           'runtime': int(entry.get('runtime') or 0), 'art': {name: art[name] for name in ART if art.get(name)}})
    data = planner.merge(read(), episodes, movies, time.time())
    save(data)
    xbmc.log('[script.aeon.helper] Planner list: %d episodes, %d films%s' % (len(data['episodes']), len(data['movies']),
                                                                         ' (kept part of the old list)' if data.get('partial') else ''), xbmc.LOGINFO)
    return data['episodes']


def publish_week(state):
    """Home > Planner week strip (0.31.0): Window(Home).Property(aeon.plw.N.day / .date / .count / .eps / .films / .albums /
    .iso), N = 1..7 from today. Recomputed when the day changes or the kept list is rewritten."""
    today = datetime.date.today()
    try:
        stamp = os.path.getmtime(path())
    except OSError:
        stamp = 0
    key = (today, stamp, arrfeed.stamp())
    if state.get('plweek') == key:
        return
    state['plweek'] = key
    home = xbmcgui.Window(10000)
    for i, (date, eps, films, albums) in enumerate(planner.week_kinds(upcoming(today, 6), today), 1):
        count = eps + films + albums
        home.setProperty('aeon.plw.%d.day' % i, xbmc.getLocalizedString(41 + date.weekday()))
        home.setProperty('aeon.plw.%d.date' % i, str(date.day))
        home.setProperty('aeon.plw.%d.count' % i, str(count) if count else '')
        # 0.3.59: the kinds apart (the tiles show an icon per kind) and the day itself (OK opens the Planner on it)
        home.setProperty('aeon.plw.%d.eps' % i, str(eps) if eps else '')
        home.setProperty('aeon.plw.%d.films' % i, str(films) if films else '')
        home.setProperty('aeon.plw.%d.albums' % i, str(albums) if albums else '')
        home.setProperty('aeon.plw.%d.iso' % i, date.isoformat())
