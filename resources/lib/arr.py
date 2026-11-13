# -*- coding: utf-8 -*-
"""Wanted titles from Radarr, Sonarr and Lidarr for the Planner (skin 0.33.0). No Kodi imports.

Each app's calendar API gives what comes out between two dates. What is already downloaded (hasFile, or an album with
track files) or not monitored is left out: the Planner shows what you are waiting for. The entries have the shape of
the Planner's own (nextaired.json): kind movie / episode / album, premiered (YYYY-MM-DD), title, showtitle, season,
episode, plot, runtime, art, more; plus source (radarr / sonarr / lidarr) and release:
  cinema     a film comes to the cinemas that day         digital   it comes out on streaming / download that day
  cinemanow  it is in the cinemas now (listed on today)    physical  it comes out on Blu-ray / DVD that day
  episode    an episode airs                              newshow   an episode of a show that is not in Kodi's library
  album      an album comes out"""
import datetime

NOW_DAYS = 120          # a film counts as "in cinemas now" this many days after its cinema release (until it is digital)

ART_NAMES = {'poster': 'poster', 'fanart': 'fanart', 'banner': 'banner', 'clearlogo': 'clearlogo', 'logo': 'clearlogo',
             'cover': 'thumb', 'disc': 'discart'}


def day(text):
    """The date part of an ISO time ('2026-11-20T00:00:00Z' -> date), None when there is none."""
    try:
        return datetime.datetime.strptime((text or '')[:10], '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def art(images, prefix=''):
    """Kodi art from the app's images (remote addresses only: a local one would carry the API key)."""
    found = {}
    for image in images or ():
        name = ART_NAMES.get((image.get('coverType') or '').lower())
        url = image.get('remoteUrl') or ''
        if name and url.startswith('http') and prefix + name not in found:
            found[prefix + name] = url
    return found


def rating(ratings):
    """(value, votes) of the TMDb rating, else IMDb's; (0, 0) when there is none."""
    ratings = ratings or {}
    for source in ('tmdb', 'imdb'):
        value = ratings.get(source)
        if isinstance(value, dict) and value.get('value'):
            return round(float(value['value']), 1), int(value.get('votes') or 0)
    if ratings.get('value'):                           # older Sonarr / Radarr: one rating
        return round(float(ratings['value']), 1), int(ratings.get('votes') or 0)
    return 0.0, 0


def in_window(date, first, last):
    return date is not None and first <= date <= last


def radarr_entries(movies, today, days):
    """Wanted films (monitored, no file) from Radarr's /api/v3/calendar or /api/v3/movie."""
    last = today + datetime.timedelta(days=days)
    out = []
    for movie in movies or ():
        if not movie.get('monitored', True) or movie.get('hasFile'):
            continue
        title = movie.get('title') or ''
        if not title:
            continue
        value, votes = rating(movie.get('ratings'))
        base = {'kind': 'movie', 'source': 'radarr', 'title': title, 'plot': movie.get('overview') or '',
                'runtime': int(movie.get('runtime') or 0) * 60, 'year': int(movie.get('year') or 0),
                'art': art(movie.get('images')),
                'more': {'genre': list(movie.get('genres') or []), 'mpaa': movie.get('certification') or '',
                         'studio': [movie['studio']] if movie.get('studio') else [], 'rating': value, 'votes': votes,
                         'cast': [], 'network': ''}}
        cinema, digital, physical = day(movie.get('inCinemas')), day(movie.get('digitalRelease')), day(movie.get('physicalRelease'))
        dates = []
        if in_window(cinema, today, last):
            dates.append(('cinema', cinema))
        elif cinema and cinema < today and (today - cinema).days <= NOW_DAYS and not (digital and digital <= today):
            dates.append(('cinemanow', today))
        if in_window(digital, today, last):
            dates.append(('digital', digital))
        if in_window(physical, today, last):
            dates.append(('physical', physical))
        for release, date in dates:
            entry = dict(base)
            entry['release'] = release
            entry['premiered'] = date.isoformat()
            out.append(entry)
    return out


def sonarr_entries(episodes, today, days, library_shows=()):
    """Episodes still to come from Sonarr's /api/v3/calendar (includeSeries=true). An episode of a show that is not in
    Kodi's library is marked newshow."""
    last = today + datetime.timedelta(days=days)
    have = set(name.lower() for name in library_shows or ())
    out = []
    for episode in episodes or ():
        if episode.get('hasFile') or not episode.get('monitored', True):
            continue
        date = day(episode.get('airDate') or episode.get('airDateUtc'))
        if not in_window(date, today, last):
            continue
        series = episode.get('series') or {}
        show = series.get('title') or ''
        if not show:
            continue
        pictures = art(series.get('images'))
        pictures.update(art(series.get('images'), 'tvshow.'))
        value, votes = rating(series.get('ratings'))
        out.append({'kind': 'episode', 'source': 'sonarr', 'release': 'episode' if show.lower() in have else 'newshow',
                    'title': episode.get('title') or '', 'showtitle': show,
                    'season': int(episode.get('seasonNumber') or 0), 'episode': int(episode.get('episodeNumber') or 0),
                    'premiered': date.isoformat(), 'plot': episode.get('overview') or '',
                    'runtime': int(series.get('runtime') or 0) * 60, 'art': pictures,
                    'more': {'genre': list(series.get('genres') or []), 'mpaa': series.get('certification') or '',
                             'studio': [], 'rating': value, 'votes': votes, 'cast': [],
                             'network': series.get('network') or '', 'showplot': series.get('overview') or ''}})
    return out


def lidarr_entries(albums, today, days):
    """Albums still to come from Lidarr's /api/v1/calendar (includeArtist=true)."""
    last = today + datetime.timedelta(days=days)
    out = []
    for album in albums or ():
        if not album.get('monitored', True):
            continue
        stats = album.get('statistics') or {}
        if int(stats.get('trackFileCount') or 0) > 0:
            continue
        date = day(album.get('releaseDate'))
        if not in_window(date, today, last):
            continue
        artist = album.get('artist') or {}
        pictures = art(album.get('images'))
        for name, url in art(artist.get('images')).items():
            if name in ('fanart', 'clearlogo', 'banner'):
                pictures.setdefault(name, url)
        if 'thumb' in pictures:
            pictures.setdefault('poster', pictures['thumb'])
        out.append({'kind': 'album', 'source': 'lidarr', 'release': 'album', 'title': album.get('title') or '',
                    'artist': artist.get('artistName') or '', 'premiered': date.isoformat(),
                    'plot': album.get('overview') or '', 'runtime': 0, 'art': pictures,
                    'more': {'genre': list(album.get('genres') or []), 'mpaa': '', 'studio': [], 'rating': 0.0,
                             'votes': 0, 'cast': [], 'network': ''}})
    return out


def combine(base, wanted):
    """The Planner's own entries plus the wanted ones. An episode the Planner already has (same show, season and
    episode) is not listed twice; a film in both is listed once, as the app's entry (it knows the kind of release)."""
    seen_eps = set(((e.get('showtitle') or '').lower(), int(e.get('season') or 0), int(e.get('episode') or 0))
                   for e in base or () if e.get('kind') != 'movie')
    films = set(((e.get('title') or '').lower(), e.get('premiered')) for e in wanted or () if e.get('kind') == 'movie')
    out = [e for e in base or () if not (e.get('kind') == 'movie' and ((e.get('title') or '').lower(), e.get('premiered')) in films)]
    for entry in wanted or ():
        if entry.get('kind') == 'episode':
            key = ((entry.get('showtitle') or '').lower(), int(entry.get('season') or 0), int(entry.get('episode') or 0))
            if key in seen_eps:
                continue
            seen_eps.add(key)
        out.append(entry)
    return out


def pick(entries, what):
    """The Planner's choice: '' everything, 'episodes' (with albums: the music side of the calendar), 'films'."""
    if what == 'films':
        return [e for e in entries if e.get('kind') == 'movie']
    if what == 'episodes':
        return [e for e in entries if e.get('kind') != 'movie']
    return list(entries)
