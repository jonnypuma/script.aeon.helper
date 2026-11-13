import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from resources.lib.counts import album_tracks, fetch_counts, QUERIES


class FetchCounts(unittest.TestCase):
    def test_reads_limits_total(self):
        calls = []

        def rpc(method, params):
            calls.append((method, params))
            return {'result': {'limits': {'start': 0, 'end': 1, 'total': 1061 if method == 'VideoLibrary.GetMovies' else 7}}}

        counts = fetch_counts(rpc)
        self.assertEqual(counts['movies'], 1061)
        self.assertEqual(counts['tvshows'], 7)
        self.assertEqual(len(calls), len(QUERIES))
        self.assertTrue(all(p['limits'] == {'start': 0, 'end': 1} for _, p in calls))

    def test_failed_query_is_zero(self):
        def rpc(method, params):
            if method.startswith('AudioLibrary'):
                raise RuntimeError('no music library')
            return {'error': {'code': -32100}}

        counts = fetch_counts(rpc)
        self.assertEqual(set(counts), set(QUERIES))
        self.assertTrue(all(v == 0 for v in counts.values()))


class AlbumTracks(unittest.TestCase):
    def test_counts_songs_of_album(self):
        calls = []

        def rpc(method, params):
            calls.append((method, params))
            return {'result': {'limits': {'start': 0, 'end': 1, 'total': 14}}}

        self.assertEqual(album_tracks(rpc, '42'), 14)
        self.assertEqual(calls[0][0], 'AudioLibrary.GetSongs')
        self.assertEqual(calls[0][1]['filter'], {'albumid': 42})

    def test_failure_is_zero(self):
        def rpc(method, params):
            raise RuntimeError('no')
        self.assertEqual(album_tracks(rpc, '7'), 0)


if __name__ == '__main__':
    unittest.main()
