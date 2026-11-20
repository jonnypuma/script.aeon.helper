# -*- coding: utf-8 -*-
"""Home > Sets (0.3.77): the movie sets you watched last, newest first.

A set counts from the moment one of its films was played: Kodi writes a film's lastplayed when it starts, so a film
stopped half way counts too, and gives each of its set items the lastplayed of the set's film played last. The list is
Kodi's own Sets list (one Files.GetDirectory call; it leaves out one-film sets when the library setting says so) sorted
by that time, without the sets nobody played. Asking every set's details instead took 0.35 s per set on a large
MySQL library. No Kodi imports: the plugin (?info=recentsets) passes the JSON-RPC result in."""
import re

SETS_DIR = 'videodb://movies/sets/'
SET_PROPERTIES = ['title', 'art', 'plot', 'lastplayed', 'playcount']
DEFAULT_LIMIT = 20
MOST = 100
_SETID = re.compile(r'/sets/(\d+)/|[?&]setid=(\d+)')


def limit(text, default=DEFAULT_LIMIT):
    """?limit= -> a count from 1 to 100; empty, zero or not a number -> default."""
    try:
        value = int(str(text).strip())
    except (TypeError, ValueError):
        return default
    return min(value, MOST) if value > 0 else default


def request(count):
    """Files.GetDirectory parameters: the library's Sets list, last played first, count of them."""
    return {'directory': SETS_DIR, 'media': 'video', 'properties': SET_PROPERTIES,
            'sort': {'method': 'lastplayed', 'order': 'descending'}, 'limits': {'start': 0, 'end': count}}


def set_path(setid):
    """The set's folder in the video library (what the skin opens and reads the films from)."""
    return 'videodb://movies/sets/%d/' % setid


def set_id(item):
    """The set id of a Files.GetDirectory item: its id, else the number in its path."""
    try:
        value = int(item.get('id') or 0)
    except (TypeError, ValueError):
        value = 0
    if value > 0:
        return value
    found = _SETID.search(item.get('file') or '')
    return int(found.group(1) or found.group(2)) if found else 0


def played(files, count):
    """Files.GetDirectory's files -> the sets with a played film, newest first, at most count, each as a dict with
    setid, label, path, art, plot, lastplayed and playcount (Kodi's: above 0 once every film of the set is watched).
    Sorted again here so the order never depends on Kodi's; equal times keep the higher set id first."""
    found = {}
    for item in files or []:
        setid = set_id(item)
        when = (item.get('lastplayed') or '').strip()
        if setid <= 0 or not when or setid in found:
            continue
        found[setid] = {'setid': setid,
                        'label': item.get('title') or item.get('label') or '',
                        'path': set_path(setid),
                        'art': dict(item.get('art') or {}),
                        'plot': item.get('plot') or '',
                        'lastplayed': when,
                        'playcount': int(item.get('playcount') or 0)}
    ordered = sorted(found.values(), key=lambda entry: (entry['lastplayed'], entry['setid']), reverse=True)
    return ordered[:count]
