# -*- coding: utf-8 -*-
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib import ssround


class Parse(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(ssround.kinds_of('today,movies,bogus'), ['movies', 'today'])
        self.assertEqual(ssround.kinds_of(''), ['movies'])
        self.assertEqual(ssround.kinds_of(None), ['movies'])

    def test_count(self):
        self.assertEqual(ssround.count_of('10'), 10)
        self.assertEqual(ssround.count_of('5'), 5)
        self.assertEqual(ssround.count_of('99'), 10)
        self.assertEqual(ssround.count_of('1'), 3)
        self.assertEqual(ssround.count_of('x'), 10)
        self.assertEqual(ssround.count_of(None), 10)


class Mix(unittest.TestCase):
    def pools(self):
        return {'movies': ['m%d' % i for i in range(10)], 'tvshows': ['t%d' % i for i in range(10)],
                'today': ['d0'], 'cinema': [], 'music': ['a%d' % i for i in range(10)]}

    def test_count_and_order_within_a_source(self):
        got = ssround.mix(self.pools(), 10, random.Random(1))
        self.assertEqual(len(got), 10)
        movies = [item for kind, item in got if kind == 'movies']
        self.assertEqual(movies, sorted(movies, key=lambda s: int(s[1:])))

    def test_mixed_and_no_repeat_in_a_row(self):
        for seed in range(30):
            got = ssround.mix(self.pools(), 10, random.Random(seed))
            kinds = [k for k, _ in got]
            self.assertGreater(len(set(kinds)), 1)
            self.assertTrue(all(a != b for a, b in zip(kinds, kinds[1:])), kinds)
            self.assertNotIn('cinema', kinds)
            self.assertLessEqual(kinds.count('today'), 1)

    def test_one_source(self):
        got = ssround.mix({'movies': ['m0', 'm1', 'm2']}, 10, random.Random(2))
        self.assertEqual(got, [('movies', 'm0'), ('movies', 'm1'), ('movies', 'm2')])

    def test_nothing(self):
        self.assertEqual(ssround.mix({'movies': [], 'today': []}, 10), [])


if __name__ == '__main__':
    unittest.main()
