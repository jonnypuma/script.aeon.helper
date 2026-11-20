# -*- coding: utf-8 -*-
"""0.3.111: the album track list in the music player controls (resources/lib/osdalbums.py, pure parts)"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import osdalbums  # noqa: E402


class OrderTest(unittest.TestCase):
    def test_by_year_then_title(self):
        albums = osdalbums.order([(3, 'B', 2010), (1, 'A', 2010), (2, 'Z', 1999), (4, 'No year', 0)])
        self.assertEqual([a[0] for a in albums], [2, 1, 3, 4])


class NeighboursTest(unittest.TestCase):
    ALB = [(10, 'First', 1990), (11, 'Second', 1995), (12, 'Third', 2001)]

    def test_middle(self):
        self.assertEqual(osdalbums.neighbours(self.ALB, 11), ((10, 'First'), (12, 'Third')))

    def test_ends(self):
        self.assertEqual(osdalbums.neighbours(self.ALB, 10), (None, (11, 'Second')))
        self.assertEqual(osdalbums.neighbours(self.ALB, 12), ((11, 'Second'), None))

    def test_unknown(self):
        self.assertEqual(osdalbums.neighbours(self.ALB, 99), (None, None))


class StartAtTest(unittest.TestCase):
    def test_disc_then_track(self):
        songs = [(5, 2, 1), (3, 1, 2), (4, 1, 1), (6, 2, 2)]
        ids, pos = osdalbums.start_at(songs, 5)
        self.assertEqual(ids, [4, 3, 5, 6])
        self.assertEqual(pos, 2)

    def test_missing_song_starts_at_the_top(self):
        self.assertEqual(osdalbums.start_at([(1, 1, 1)], 9), ([1], 0))


if __name__ == '__main__':
    unittest.main()
