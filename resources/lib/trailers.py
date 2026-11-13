# -*- coding: utf-8 -*-
"""Find the trailer file that sits next to a film, show, season or episode. No Kodi imports.

Sidecar names seen in libraries: "<video file name>-trailer.mkv", "movie-trailer.mp4", "tvshow-trailer.mp4",
"season01-trailer.mkv", "trailer.mp4". A local file is always preferred; the trailer address the library holds
(usually YouTube) is only the fallback."""
import re

VIDEO = ('.mkv', '.mp4', '.m4v', '.avi', '.mov', '.webm', '.ts', '.wmv', '.mpg', '.mpeg')


def stem(name):
    dot = name.rfind('.')
    return name[:dot] if dot > 0 else name


def is_trailer(name):
    lower = name.lower()
    return lower.endswith(VIDEO) and re.search(r'(^|[-_. ])trailer$', stem(lower)) is not None


def pick(names, kind='movie', base='', season=None):
    """The best trailer among the file names of a folder, or ''.

    kind: movie / tvshow / season / episode. base: name of the video file without extension (movie, episode).
    season: number, for a season."""
    candidates = [name for name in names or () if is_trailer(name)]
    if not candidates:
        return ''
    by_stem = {stem(name).lower(): name for name in candidates}

    def first(*stems):
        for wanted in stems:
            if wanted and wanted.lower() in by_stem:
                return by_stem[wanted.lower()]
        return ''

    if kind == 'episode':
        return first(base + '-trailer') if base else ''          # never the show's trailer for one episode
    if kind == 'season':
        number = int(season) if season not in (None, '') else -1
        if number >= 0:
            found = first('season%02d-trailer' % number, 'season%d-trailer' % number, 'season-trailer')
            if found:
                return found
        return first('tvshow-trailer', 'trailer')
    if kind == 'tvshow':
        found = first('tvshow-trailer', 'trailer')
        if found:
            return found
        others = sorted(name for name in candidates if not stem(name).lower().startswith('season'))
        return others[0] if others else ''
    # movie: its own sidecar first, then the generic names, then the only trailer in the folder
    found = first(base + '-trailer' if base else '', 'movie-trailer', 'trailer')
    if found:
        return found
    return candidates[0] if len(candidates) == 1 else ''
