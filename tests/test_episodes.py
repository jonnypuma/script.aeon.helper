import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from resources.lib.episodes import fetch_epmark


def rpc_for(season, number, last_in_season, seasons, status):
    def rpc(method, params):
        if method == 'VideoLibrary.GetEpisodeDetails':
            return {'result': {'episodedetails': {'season': season, 'episode': number, 'tvshowid': 1}}}
        if method == 'VideoLibrary.GetEpisodes':
            return {'result': {'episodes': [{'episode': n} for n in range(1, last_in_season + 1)]}}
        if method == 'VideoLibrary.GetSeasons':
            return {'result': {'seasons': [{'season': s} for s in range(1, seasons + 1)]}}
        return {'result': {'tvshowdetails': {'status': status}}}
    return rpc


def test_marks():
    assert fetch_epmark(rpc_for(1, 1, 8, 2, 'Continuing'), 'episode', 5) == 'series_premiere'
    assert fetch_epmark(rpc_for(2, 1, 8, 2, 'Continuing'), 'episode', 5) == 'season_premiere'
    assert fetch_epmark(rpc_for(1, 8, 8, 2, 'Continuing'), 'episode', 5) == 'season_finale'
    assert fetch_epmark(rpc_for(2, 8, 8, 2, 'Ended'), 'episode', 5) == 'series_finale'
    assert fetch_epmark(rpc_for(2, 8, 8, 2, 'Continuing'), 'episode', 5) == 'season_finale'
    assert fetch_epmark(rpc_for(1, 3, 8, 2, 'Ended'), 'episode', 5) == ''
    assert fetch_epmark(rpc_for(1, 3, 8, 2, 'Ended'), 'movie', 5) == ''


def test_no_finale_while_more_airs():
    """0.3.115: S3 E6 is the last in the library, E7 airs next week: no season finale"""
    base = rpc_for(3, 6, 6, 3, 'Continuing')

    def rpc(method, params):
        if method == 'VideoLibrary.GetTVShowDetails' and 'title' in params.get('properties', []):
            return {'result': {'tvshowdetails': {'title': 'The Rings of Power'}}}
        return base(method, params)
    later = [{'showtitle': 'The Rings of Power', 'season': 3, 'episode': 7, 'premiered': '2026-11-25'}]
    assert fetch_epmark(rpc, 'episode', 5, upcoming=later) == ''
    assert fetch_epmark(rpc, 'episode', 5, upcoming=[{'showtitle': 'Other', 'season': 3, 'episode': 7}]) == 'season_finale'
    assert fetch_epmark(rpc, 'episode', 5, upcoming=[]) == 'season_finale'
