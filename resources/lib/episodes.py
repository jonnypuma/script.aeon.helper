"""Premiere / finale marks for an episode. Pure logic: the caller passes the rpc function."""


def _result(rpc, method, params, key):
    try:
        return (rpc(method, params) or {}).get('result', {}).get(key)
    except Exception:
        return None


def fetch_epmark(rpc, dbtype, dbid):
    """'series_premiere' | 'season_premiere' | 'series_finale' | 'season_finale' | '' for an episode."""
    if dbtype != 'episode':
        return ''
    try:
        dbid = int(dbid)
    except (TypeError, ValueError):
        return ''
    ep = _result(rpc, 'VideoLibrary.GetEpisodeDetails',
                 {'episodeid': dbid, 'properties': ['season', 'episode', 'tvshowid']}, 'episodedetails')
    if not ep:
        return ''
    season, number, show = ep.get('season', 0), ep.get('episode', 0), ep.get('tvshowid', 0)
    if season <= 0 or number <= 0:
        return ''
    if number == 1:
        return 'series_premiere' if season == 1 else 'season_premiere'
    eps = _result(rpc, 'VideoLibrary.GetEpisodes',
                  {'tvshowid': show, 'season': season, 'properties': ['episode']}, 'episodes') or []
    if not eps or number < max(e.get('episode', 0) for e in eps):
        return ''
    seasons = _result(rpc, 'VideoLibrary.GetSeasons', {'tvshowid': show, 'properties': ['season']}, 'seasons') or []
    last_season = max([s.get('season', 0) for s in seasons] or [season])
    status = (_result(rpc, 'VideoLibrary.GetTVShowDetails', {'tvshowid': show, 'properties': ['status']},
                      'tvshowdetails') or {}).get('status', '')
    if season >= last_season and status.lower() == 'ended':
        return 'series_finale'
    return 'season_finale'
