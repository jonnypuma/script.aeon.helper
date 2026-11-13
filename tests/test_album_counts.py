import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib.counts import album_counts


class AlbumCounts(unittest.TestCase):
    def test_counts_per_album_artist(self):
        def rpc(method, params):
            self.assertEqual(method, 'AudioLibrary.GetAlbums')
            return {'result': {'albums': [{'artistid': [1]}, {'artistid': [1, 2]}, {'artistid': []}, {}]}}
        self.assertEqual(album_counts(rpc), {'1': 2, '2': 1})

    def test_failed_query(self):
        def rpc(method, params):
            raise RuntimeError('no library')
        self.assertEqual(album_counts(rpc), {})

    def test_empty_reply(self):
        self.assertEqual(album_counts(lambda m, p: None), {})


if __name__ == '__main__':
    unittest.main()
