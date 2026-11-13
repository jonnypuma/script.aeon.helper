# -*- coding: utf-8 -*-
"""Cinema mode: which trailers to show before a film. No Kodi imports.

The pool is a list of films from the TMDb Helper lists "In cinemas now", "Upcoming", "Trending" and "Popular", as dicts with title, premiered
(YYYY-MM-DD) and trailer (a playable path). Only new films count: released at most RECENT days ago or due within AHEAD
days. Films without a trailer or a date are left out."""
import datetime
import random

RECENT = 60       # days since release
AHEAD = 180       # days until release
# what is in cinemas (three pages), what is coming, and what is talked about: the last two are mostly older films
# or carry no trailer, the date window and the trailer check keep only what fits
LISTS = ('now_playing&page=1', 'now_playing&page=2', 'now_playing&page=3', 'upcoming&page=1', 'upcoming&page=2',
         'trending_week&page=1', 'popular&page=1')
PLUGIN = 'plugin://plugin.video.themoviedb.helper/?info=%s&tmdb_type=movie'


def parse_date(text):
    try:
        return datetime.datetime.strptime((text or '')[:10], '%Y-%m-%d').date()
    except ValueError:
        return None


def is_new(premiered, today):
    date = parse_date(premiered)
    if date is None:
        return False
    return -RECENT <= (date - today).days <= AHEAD


def build_pool(files, today):
    """Files.GetDirectory entries -> [{'title', 'premiered', 'trailer'}], new films with a trailer, each trailer once."""
    pool = []
    seen = set()
    for entry in files or ():
        trailer = entry.get('trailer') or ''
        if not trailer or trailer in seen or not is_new(entry.get('premiered'), today):
            continue
        seen.add(trailer)
        pool.append({'title': entry.get('title') or entry.get('label') or '', 'premiered': entry['premiered'][:10], 'trailer': trailer})
    return pool


def pick(pool, count, today, rng=random):
    """Up to count different trailers, at random, from the films that are still new today."""
    fresh = [film for film in pool or () if is_new(film.get('premiered'), today)]
    if count <= 0 or not fresh:
        return []
    return rng.sample(fresh, min(count, len(fresh)))


def wanted(setting):
    """Skin.String(aeon.cinema) -> number of trailers (0 = off)."""
    return int(setting) if setting in ('1', '2', '3') else 0


def should_intercept(media_type, dbid, playlist_size, position_seconds):
    """A library film started on its own from the beginning; not a resumed film, not an item of a playlist (ours included)."""
    return media_type == 'movie' and dbid > 0 and playlist_size <= 1 and position_seconds < 15
