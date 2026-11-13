import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from resources.lib.ratings import fetch_ratings


def make_rpc(ratings):
    return lambda method, params: {'result': {'episodedetails': {'ratings': ratings}}}


def test_all_sources():
    rpc = make_rpc({'imdb': {'rating': 6.7}, 'trakt': {'rating': 7.5}, 'themoviedb': {'rating': 8.0}})
    assert fetch_ratings(rpc, 'episode', '5') == {'imdb': '6.7', 'trakt': '7.5', 'tmdb': '8.0'}


def test_unknown_type_or_id():
    assert fetch_ratings(make_rpc({}), 'song', '5') == {}
    assert fetch_ratings(make_rpc({}), 'episode', '') == {}


def test_failed_rpc():
    def boom(*a):
        raise RuntimeError
    assert fetch_ratings(boom, 'episode', '5') == {}
