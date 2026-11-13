# -*- coding: utf-8 -*-
"""Match the titles of an online list (TMDb Helper) against the video library. No Kodi imports.

A title is in the library when the TMDb id is the same, or - for entries without one - when title and year are."""
import re
import unicodedata

LISTS = ('trending_day', 'trending_week', 'popular', 'top_rated', 'now_playing', 'upcoming', 'on_the_air', 'airing_today',
         'recommendations', 'similar')


def norm(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def plain(label):
    """A label without Kodi markup ([COLOR=..], [I], [B] ...)."""
    return re.sub(r'\[/?(?:COLOR|I|B|UPPERCASE|LOWERCASE|CAPITALIZE|LIGHT)[^\]]*\]', '', label or '').strip()


def year_of(entry):
    year = entry.get('year') or 0
    if not year:
        text = entry.get('premiered') or entry.get('firstaired') or ''
        year = int(text[:4]) if text[:4].isdigit() else 0
    return int(year)


def index(library, idkey):
    """library: [{idkey, 'title'/'label', 'year', 'uniqueid': {'tmdb': ..}}] -> ({tmdb id: dbid}, {(title, year): dbid of items without a TMDb id})."""
    by_tmdb = {}
    by_title = {}
    for item in library or ():
        dbid = item.get(idkey)
        if not dbid:
            continue
        tmdb = str((item.get('uniqueid') or {}).get('tmdb') or '')
        if tmdb:
            by_tmdb.setdefault(tmdb, dbid)
            continue                        # known by its id: never matched by title, so a remake is not mistaken for it
        key = (norm(item.get('title') or item.get('label')), int(item.get('year') or 0))
        if key[0]:
            by_title.setdefault(key, dbid)
    return by_tmdb, by_title


def find(entry, by_tmdb, by_title):
    """Library id of one online entry, or None."""
    tmdb = str((entry.get('uniqueid') or {}).get('tmdb') or '')
    if tmdb and tmdb in by_tmdb:
        return by_tmdb[tmdb]
    # library items without a TMDb id (IMDb or TVDB numbered) are matched by title and year
    return by_title.get((norm(plain(entry.get('title') or entry.get('label'))), year_of(entry)))


def build_path(info, tmdb_type, query='', year=''):
    """The TMDb Helper path of a list; None for a list or type that is not offered."""
    if info not in LISTS or tmdb_type not in ('movie', 'tv'):
        return None
    path = 'plugin://plugin.video.themoviedb.helper/?info=%s&tmdb_type=%s' % (info, tmdb_type)
    if info in ('recommendations', 'similar'):
        if not query:
            return None
        path += '&query=%s' % query
        if year:
            path += '&year=%s' % year
    return path
