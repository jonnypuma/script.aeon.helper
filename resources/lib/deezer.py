# -*- coding: utf-8 -*-
"""Top tracks and related artists from Deezer's public API (no key), matched against the library. No Kodi imports.

Every function takes fetch(url) -> parsed JSON (raises or returns None on failure), so the logic is testable offline.
Only the artist's name is sent to Deezer."""
import re
import unicodedata

try:
    from urllib.parse import quote
except ImportError:                      # pragma: no cover
    from urllib import quote

API = 'https://api.deezer.com'
BRACKETS = re.compile(r'\s*[\(\[][^\)\]]*[\)\]]')
FEAT = re.compile(r'\s+(feat\.?|ft\.?|featuring)\s.*$', re.I)


def norm(text):
    """Comparable form of a name or title: no accents, case, brackets, 'feat. x' tails, 'the ' or punctuation."""
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(ch for ch in text if not unicodedata.combining(ch)).lower()
    text = FEAT.sub('', BRACKETS.sub('', text))
    text = text.replace('&', ' and ')
    text = re.sub(r'[^a-z0-9]+', ' ', text).strip()
    return text[4:] if text.startswith('the ') else text


def find_artist(fetch, name):
    """Deezer id of the artist called name: among exact (normalised) name matches the one with most fans. None if none."""
    if not norm(name):
        return None
    reply = fetch('%s/search/artist?limit=10&q=%s' % (API, quote(name.encode('utf-8')))) or {}
    exact = [entry for entry in reply.get('data') or () if norm(entry.get('name')) == norm(name)]
    if not exact:
        return None
    return max(exact, key=lambda entry: entry.get('nb_fan') or 0).get('id')


def top_tracks(fetch, deezer_id, limit=12):
    """[{'title', 'album', 'cover'}] in Deezer's order (most popular first), each normalised title once."""
    reply = fetch('%s/artist/%d/top?limit=%d' % (API, deezer_id, limit * 2)) or {}
    tracks = []
    seen = set()
    for entry in reply.get('data') or ():
        key = norm(entry.get('title'))
        if not key or key in seen:
            continue
        seen.add(key)
        album = entry.get('album') or {}
        tracks.append({'title': entry.get('title') or '', 'album': album.get('title') or '', 'cover': album.get('cover_medium') or ''})
    return tracks[:limit]


def related(fetch, deezer_id, limit=20):
    """[{'name', 'picture'}] in Deezer's order."""
    reply = fetch('%s/artist/%d/related?limit=%d' % (API, deezer_id, limit)) or {}
    return [{'name': entry.get('name') or '', 'picture': entry.get('picture_medium') or ''}
            for entry in reply.get('data') or () if entry.get('name')]


def lookup(fetch, name):
    """{'tracks': [...], 'related': [...]} for an artist name; None when Deezer does not know the artist."""
    deezer_id = find_artist(fetch, name)
    if not deezer_id:
        return None
    return {'tracks': top_tracks(fetch, deezer_id), 'related': related(fetch, deezer_id)}


def match_tracks(tracks, songs):
    """Pair each Deezer track with a library song of the same (normalised) title, or None. songs: [{'title', ...}].
    Of several library versions the one with exactly the same title wins, then the most played one."""
    by_title = {}
    for song in songs or ():
        by_title.setdefault(norm(song.get('title') or song.get('label')), []).append(song)
    pairs = []
    for track in tracks or ():
        versions = by_title.get(norm(track['title'])) or []
        wanted = (track['title'] or '').strip().lower()
        best = max(versions, key=lambda song: ((song.get('title') or '').strip().lower() == wanted, song.get('playcount') or 0)) if versions else None
        pairs.append((track, best))
    return pairs


def match_artists(names, artists):
    """Pair each related artist with the library artist of the same (normalised) name, or None. artists: [{'artistid', 'label'}]."""
    by_name = {}
    for artist in artists or ():
        by_name.setdefault(norm(artist.get('label')), artist)
    return [(entry, by_name.get(norm(entry['name']))) for entry in names or ()]
