import datetime
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib.cinema import build_pool, is_new, pick, should_intercept, wanted

TODAY = datetime.date(2026, 11, 11)


def film(title, premiered, trailer):
    return {'title': title, 'premiered': premiered, 'trailer': trailer}


class Cinema(unittest.TestCase):
    def test_new_window(self):
        self.assertTrue(is_new('2026-11-03', TODAY))          # in cinemas now
        self.assertTrue(is_new('2027-02-01', TODAY))          # upcoming
        self.assertFalse(is_new('2026-03-20', TODAY))         # old
        self.assertFalse(is_new('2028-01-01', TODAY))         # too far ahead
        self.assertFalse(is_new('', TODAY))
        self.assertFalse(is_new('soon', TODAY))

    def test_pool_drops_old_dateless_trailerless_and_doubles(self):
        files = [film('A', '2026-11-03', 't1'), film('Old', '2020-01-01', 't2'), film('NoTrailer', '2026-11-05', ''),
                 film('NoDate', '', 't3'), film('A again', '2026-11-04', 't1'), {'label': 'B', 'premiered': '2026-12-01T00:00', 'trailer': 't4'}]
        pool = build_pool(files, TODAY)
        self.assertEqual([f['trailer'] for f in pool], ['t1', 't4'])
        self.assertEqual(pool[1], {'title': 'B', 'premiered': '2026-12-01', 'trailer': 't4'})

    def test_pick_count_and_distinct(self):
        pool = [film(str(i), '2026-11-10', 't%d' % i) for i in range(6)]
        got = pick(pool, 3, TODAY, random.Random(1))
        self.assertEqual(len(got), 3)
        self.assertEqual(len({f['trailer'] for f in got}), 3)

    def test_pick_small_pool_and_off(self):
        pool = [film('A', '2026-11-10', 't1')]
        self.assertEqual(len(pick(pool, 3, TODAY)), 1)
        self.assertEqual(pick(pool, 0, TODAY), [])
        self.assertEqual(pick([], 2, TODAY), [])

    def test_pick_skips_films_that_went_stale_in_the_cache(self):
        pool = [film('A', '2026-11-10', 't1')]
        self.assertEqual(pick(pool, 1, datetime.date(2027, 6, 1)), [])

    def test_wanted(self):
        self.assertEqual([wanted(v) for v in ('', '1', '2', '3', '4', 'x')], [0, 1, 2, 3, 0, 0])

    def test_should_intercept(self):
        self.assertTrue(should_intercept('movie', 12, 1, 0.4))
        self.assertTrue(should_intercept('movie', 12, 0, 0.4))
        self.assertFalse(should_intercept('movie', 12, 1, 600))       # resumed
        self.assertFalse(should_intercept('movie', 12, 3, 0))         # part of a playlist (also our own)
        self.assertFalse(should_intercept('episode', 12, 1, 0))
        self.assertFalse(should_intercept('movie', -1, 1, 0))         # not from the library (a trailer)
        self.assertFalse(should_intercept('', 0, 1, 0))


if __name__ == '__main__':
    unittest.main()
