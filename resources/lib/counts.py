"""Library counts through JSON-RPC. Pure logic: the caller passes the rpc function, so this runs outside Kodi."""

WATCHED = {'field': 'playcount', 'operator': 'greaterthan', 'value': '0'}

# property suffix -> (JSON-RPC method, extra params)
QUERIES = {
    'movies': ('VideoLibrary.GetMovies', {}),
    'tvshows': ('VideoLibrary.GetTVShows', {}),
    'episodes': ('VideoLibrary.GetEpisodes', {}),
    'musicvideos': ('VideoLibrary.GetMusicVideos', {}),
    'artists': ('AudioLibrary.GetArtists', {}),
    'albums': ('AudioLibrary.GetAlbums', {}),
    'songs': ('AudioLibrary.GetSongs', {}),
    'movies.watched': ('VideoLibrary.GetMovies', {'filter': WATCHED}),
    'tvshows.watched': ('VideoLibrary.GetTVShows', {'filter': WATCHED}),
    'episodes.watched': ('VideoLibrary.GetEpisodes', {'filter': WATCHED}),
}


def fetch_counts(rpc):
    """rpc(method, params) -> the decoded JSON-RPC reply (dict). Returns {name: int}; a failed query gives 0."""
    out = {}
    for name, (method, extra) in QUERIES.items():
        params = dict(extra)
        # one item is enough: Kodi reports the full size in limits.total
        params['limits'] = {'start': 0, 'end': 1}
        try:
            reply = rpc(method, params) or {}
            out[name] = int(reply.get('result', {}).get('limits', {}).get('total', 0))
        except Exception:
            out[name] = 0
    return out


def album_counts(rpc):
    """{artist id (str): number of albums the artist is an album artist of}. One query for the whole library."""
    out = {}
    try:
        reply = rpc('AudioLibrary.GetAlbums', {'properties': ['artistid']}) or {}
        albums = reply.get('result', {}).get('albums', []) or []
    except Exception:
        return out
    for album in albums:
        for artist in album.get('artistid') or []:
            key = str(artist)
            out[key] = out.get(key, 0) + 1
    return out


def album_tracks(rpc, albumid):
    """Number of songs on the album with this library id (0 if unknown). Kodi gives no song count for albums, so the
    songs are counted: one item asked for, the total read from limits."""
    try:
        reply = rpc('AudioLibrary.GetSongs', {'filter': {'albumid': int(albumid)}, 'limits': {'start': 0, 'end': 1},
                                              'properties': []}) or {}
        return int(reply.get('result', {}).get('limits', {}).get('total', 0))
    except Exception:
        return 0
