import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib import inlibrary


class FakeRpc(object):
    def __init__(self):
        self.calls = []

    def __call__(self, method, params):
        self.calls.append(method)
        if method == 'VideoLibrary.GetTVShows':
            shows = [{'tvshowid': 7, 'title': 'The Blacklist'}, {'tvshowid': 9, 'title': 'Dexter: Resurrection'}]
            want = ' '.join(params['filter']['value'].lower().split())
            return {'tvshows': [x for x in shows if x['title'].lower() == want]}
        if method == 'VideoLibrary.GetEpisodes' and 'filter' in params:
            have = [('The Blacklist', 3, 18, 'nfs://a.mkv'), ('The Blacklist', 3, 19, ''), ('Dexter: Resurrection', 2, 3, 'nfs://d.mkv')]
            out = []
            for rule in params['filter']['or']:
                show, season, number = [r['value'] for r in rule['and']]
                out += [{'showtitle': h[0], 'season': h[1], 'episode': h[2], 'file': h[3]} for h in have
                        if h[0].lower() == show.lower() and str(h[1]) == season and str(h[2]) == number]
            return {'episodes': out}
        if method == 'VideoLibrary.GetMovies' and 'or' in params['filter']:
            titles = [r['value'].lower() for r in params['filter']['or']]
            return {'movies': [{'title': 'Butterfly', 'year': 2025, 'file': 'nfs://b.mkv'}] if 'butterfly' in titles else []}
        if method == 'VideoLibrary.GetEpisodes':
            if params['tvshowid'] == 7:
                return {'episodes': [{'season': 3, 'episode': 18, 'file': 'nfs://a.mkv'}, {'season': 3, 'episode': 19, 'file': ''}]}
            return {'episodes': [{'season': 2, 'episode': 3, 'file': 'nfs://d.mkv'}]}
        if method == 'VideoLibrary.GetMovies':
            if params['filter']['value'] == 'Butterfly':
                return {'movies': [{'year': 2025, 'file': 'nfs://b.mkv'}]}
            return {'movies': []}
        if method == 'AudioLibrary.GetAlbums':
            if params['filter']['value'] == 'Tubular Bells':
                return {'albums': [{'artist': ['Mike Oldfield']}]}
            return {'albums': []}
        return {}


class InLibrary(unittest.TestCase):
    def test_episodes(self):
        rpc = FakeRpc()
        look = inlibrary.Lookup(rpc)
        self.assertTrue(look.has({'kind': 'episode', 'showtitle': 'the blacklist', 'season': 3, 'episode': 18}))
        self.assertFalse(look.has({'kind': 'episode', 'showtitle': 'The Blacklist', 'season': 3, 'episode': 19}))   # no file
        self.assertFalse(look.has({'kind': 'episode', 'showtitle': 'The Blacklist', 'season': 3, 'episode': 20}))
        self.assertTrue(look.has({'showtitle': 'Dexter:  Resurrection', 'season': '2', 'episode': '3'}))
        self.assertFalse(look.has({'showtitle': 'Unknown Show', 'season': 1, 'episode': 1}))
        self.assertEqual(rpc.calls.count('VideoLibrary.GetTVShows'), 3)      # once per title asked
        self.assertEqual(rpc.calls.count('VideoLibrary.GetEpisodes'), 2)      # once per show

    def test_films(self):
        look = inlibrary.Lookup(FakeRpc())
        self.assertTrue(look.has({'kind': 'movie', 'title': 'Butterfly', 'premiered': '2026-11-13'}))   # a year apart
        self.assertFalse(look.has({'kind': 'movie', 'title': 'Butterfly', 'year': 2019}))
        self.assertFalse(look.has({'kind': 'movie', 'title': 'Clayface', 'premiered': '2026-11-13'}))

    def test_albums(self):
        look = inlibrary.Lookup(FakeRpc())
        self.assertTrue(look.has({'kind': 'album', 'title': 'Tubular Bells', 'artist': 'Mike Oldfield'}))
        self.assertFalse(look.has({'kind': 'album', 'title': 'Tubular Bells', 'artist': 'Someone Else'}))
        self.assertFalse(look.has({'kind': 'album', 'title': 'Ommadawn', 'artist': 'Mike Oldfield'}))

    def test_prefetch_asks_once(self):
        rpc = FakeRpc()
        look = inlibrary.Lookup(rpc)
        day = [{'kind': 'episode', 'showtitle': 'The Blacklist', 'season': 3, 'episode': 18},
               {'kind': 'episode', 'showtitle': 'The Blacklist', 'season': 3, 'episode': 19},
               {'kind': 'episode', 'showtitle': 'Dexter: Resurrection', 'season': 2, 'episode': 3},
               {'kind': 'movie', 'title': 'Butterfly', 'premiered': '2026-11-13'},
               {'kind': 'movie', 'title': 'Clayface', 'premiered': '2026-11-13'}]
        look.prefetch(day)
        self.assertEqual([look.has(e) for e in day], [True, False, True, True, False])
        self.assertEqual(rpc.calls, ['VideoLibrary.GetEpisodes', 'VideoLibrary.GetMovies'])

    def test_rpc_failure_is_not_in_library(self):
        def broken(method, params):
            raise RuntimeError('no')
        self.assertFalse(inlibrary.Lookup(broken).has({'showtitle': 'X', 'season': 1, 'episode': 1}))


if __name__ == '__main__':
    unittest.main()
