# -*- coding: utf-8 -*-
"""Artists in the library that resemble a given artist, by the genres of their songs. No Kodi imports.

A genre shared by few artists says more than one nearly everybody has ("Rock"), so each shared genre counts by its
rarity. The score is divided by the size of the other artist's genre list, so an artist tagged with everything does
not match everyone."""
import json
import math

try:
    from urllib.parse import quote
except ImportError:                      # pragma: no cover
    from urllib import quote


def genres_of(artist):
    """Lower-case genre names of one AudioLibrary.GetArtists entry (properties songgenres and genre) or of a cached entry, blanks dropped."""
    if 'genres' in artist:                 # an entry of the helper's cache
        return {name.strip().lower() for name in artist['genres'] if name and name.strip()}
    names = [entry.get('title', '') for entry in artist.get('songgenres') or ()]
    names.extend(artist.get('genre') or ())
    return {name.strip().lower() for name in names if name and name.strip()}


def rank(artists, artistid, count=12):
    """Names of up to count artists most like artistid, best first. [] when the artist is unknown or has no genres."""
    tagged = [(artist, genres_of(artist)) for artist in artists or ()]
    mine = next((genres for artist, genres in tagged if artist.get('artistid') == artistid), None)
    if not mine:
        return []
    total = len(tagged)
    spread = {}
    for _artist, genres in tagged:
        for genre in genres:
            spread[genre] = spread.get(genre, 0) + 1
    scored = []
    for artist, genres in tagged:
        if artist.get('artistid') == artistid or not genres:
            continue
        shared = mine & genres
        if not shared:
            continue
        score = sum(math.log(float(total) / spread[genre]) for genre in shared) / math.sqrt(len(genres))
        if score > 0:
            scored.append((score, artist.get('label') or artist.get('artist') or ''))
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [name for _score, name in scored[:count] if name]


def artists_path(names):
    """A library path that lists exactly these artists ('' for none). The names are URL-encoded, so any character is safe."""
    if not names:
        return ''
    xsp = {'type': 'artists', 'rules': {'or': [{'field': 'artist', 'operator': 'is', 'value': list(names)}]}}
    return 'musicdb://artists/?albumartistsonly=false&xsp=' + quote(json.dumps(xsp))


def tracks_path(artistid):
    return 'musicdb://songs/?artistid=%d' % artistid
