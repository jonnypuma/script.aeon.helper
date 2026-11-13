"""All ratings of the focused library item. Pure logic: the caller passes the rpc function.

Kodi's directory listings only carry the default rating of an item (ListItem.Rating(trakt) is empty in a list
even when the library has it); the info dialog loads the full set. This fetches the full set so the skin can show
every source in every view.
"""

# DBType -> (method, id param, result key)
DETAILS = {
    'movie': ('VideoLibrary.GetMovieDetails', 'movieid', 'moviedetails'),
    'tvshow': ('VideoLibrary.GetTVShowDetails', 'tvshowid', 'tvshowdetails'),
    'episode': ('VideoLibrary.GetEpisodeDetails', 'episodeid', 'episodedetails'),
    'musicvideo': ('VideoLibrary.GetMusicVideoDetails', 'musicvideoid', 'musicvideodetails'),
}

# Kodi rating key -> skin property suffix
SOURCES = {
    'imdb': 'imdb',
    'themoviedb': 'tmdb',
    'tmdb': 'tmdb',
    'trakt': 'trakt',
    'tomatometerallcritics': 'rt',
}
NAMES = ('imdb', 'tmdb', 'trakt', 'rt')


def fetch_ratings(rpc, dbtype, dbid):
    """Returns {'imdb': '6.7', ...} for the sources the item has (empty dict when unknown)."""
    spec = DETAILS.get(dbtype)
    try:
        dbid = int(dbid)
    except (TypeError, ValueError):
        return {}
    if not spec or dbid <= 0:
        return {}
    method, idparam, key = spec
    try:
        reply = rpc(method, {idparam: dbid, 'properties': ['ratings']}) or {}
        ratings = reply.get('result', {}).get(key, {}).get('ratings', {}) or {}
    except Exception:
        return {}
    out = {}
    for source, info in ratings.items():
        name = SOURCES.get(source)
        if not name or name in out:
            continue
        try:
            value = float(info.get('rating', 0))
        except (TypeError, ValueError):
            continue
        if value > 0:
            out[name] = '%.1f' % value
    return out
