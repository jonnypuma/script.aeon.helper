# -*- coding: utf-8 -*-
"""The spotlight of a favourite on Fused Glass Home > Favourites (0.3.73): which episode of a show to continue, how much
of it is left, the next airing and the tile shape. No Kodi imports: the plugin passes JSON-RPC results and texts in."""
import datetime

WIDE = ('tvshow', 'episode')
POSTER = ('movie', 'set')
GLYPHS = {'folder': 'common/aeon_mi_folder.png', 'window': 'aeon/icons/grid.png', 'file': 'aeon/icons/film.png',
          'song': 'aeon/icons/music.png', 'addon': 'common/aeon_mi_box.png', 'channel': 'aeon/icons/tv.png',
          'playlist': 'aeon/icons/clock.png'}


def shape(what):
    """'wide' (16:9, shows), 'poster' (2:3, films and sets) or 'square' (everything else)."""
    return 'wide' if what in WIDE else ('poster' if what in POSTER else 'square')


def is_playlist(path):
    low = (path or '').lower()
    return low.endswith(('.xsp', '.m3u', '.m3u8', '.pls')) or 'playlist' in low


def tile_art(what, art, thumb=''):
    """The picture for a tile of this shape: shows landscape (else fanart), episodes their thumb, films poster, others the
    thumb / icon."""
    art = art or {}
    kind = shape(what)
    if what == 'episode':                    # an episode saved as a file: its own thumb (0.3.76)
        return art.get('thumb') or thumb or art.get('landscape') or art.get('fanart')
    if kind == 'wide':
        return art.get('landscape') or art.get('fanart') or art.get('thumb') or thumb
    if kind == 'poster':
        return art.get('poster') or art.get('thumb') or thumb
    return art.get('thumb') or art.get('poster') or art.get('icon') or thumb


def episode_tag(season, episode):
    return 'S%d E%d' % (int(season or 0), int(episode or 0))


def continue_episode(episodes):
    """Episodes of one show (JSON-RPC: season, episode, playcount, resume, lastplayed ...) -> (episode, in_progress,
    more): the episode started last if one is part watched, else the first unwatched one (specials, season 0, last);
    more = unwatched episodes after it in the same season. (None, False, 0) when everything was watched."""
    eps = sorted((e for e in episodes or () if e.get('season') is not None),
                 key=lambda e: (int(e.get('season') or 0) == 0, int(e.get('season') or 0), int(e.get('episode') or 0)))
    started = [e for e in eps if ((e.get('resume') or {}).get('position') or 0) > 0]
    if started:
        chosen = max(started, key=lambda e: e.get('lastplayed') or '')
        in_progress = True
    else:
        unwatched = [e for e in eps if not e.get('playcount')]
        if not unwatched:
            return None, False, 0
        chosen, in_progress = unwatched[0], False
    season, number = int(chosen.get('season') or 0), int(chosen.get('episode') or 0)
    more = sum(1 for e in eps if int(e.get('season') or 0) == season and int(e.get('episode') or 0) > number
               and not e.get('playcount'))
    return chosen, in_progress, more


def progress(item):
    """(percent played 0-100, minutes left) from a JSON-RPC item with resume {position, total} and runtime (seconds)."""
    resume = item.get('resume') or {}
    position = float(resume.get('position') or 0)
    total = float(resume.get('total') or 0) or float(item.get('runtime') or 0)
    if total <= 0:
        return 0, 0
    pct = int(round(100 * position / total)) if position > 0 else 0
    left = int(round((total - position) / 60.0))
    return max(0, min(100, pct)), max(0, left)


def next_airing(entries, showtitle, today):
    """The first kept next-aired entry (nextaired.json: showtitle, season, episode, premiered) of this show from today
    on, or None."""
    want = (showtitle or '').strip().lower()
    found = [e for e in entries or () if (e.get('showtitle') or '').strip().lower() == want
             and (e.get('premiered') or '') >= today.isoformat()]
    return min(found, key=lambda e: (e.get('premiered'), e.get('season') or 0, e.get('episode') or 0)) if found else None


def air_date(premiered, today, weekdays, months, words=None):
    """'2026-11-18' -> 'Wednesday 18 November' (weekdays Monday..Sunday, months January..December in the user's
    language); today / tomorrow use words['today'] / words['tomorrow'] when given."""
    try:
        date = datetime.datetime.strptime(premiered[:10], '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return ''
    words = words or {}
    if date == today and words.get('today'):
        day = words['today']
    elif date == today + datetime.timedelta(days=1) and words.get('tomorrow'):
        day = words['tomorrow']
    else:
        day = weekdays[date.weekday()]
    return '%s %d %s' % (day, date.day, months[date.month - 1])


def fill(pattern, **values):
    """A translated pattern with {name} fields; a pattern that lost a field keeps working."""
    try:
        return pattern.format(**values)
    except (KeyError, IndexError, ValueError):
        return pattern
