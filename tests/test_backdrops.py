# -*- coding: utf-8 -*-
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import backdrops


class TestBackdrops(unittest.TestCase):
    def test_add_moves_to_top_without_repeats(self):
        p = backdrops.add([], 'a.jpg')
        p = backdrops.add(p, 'b.jpg')
        p = backdrops.add(p, 'a.jpg')
        self.assertEqual(p, ['a.jpg', 'b.jpg'])
        self.assertEqual(backdrops.add(p, ''), p)

    def test_limit(self):
        p = []
        for i in range(60):
            p = backdrops.add(p, '%d.jpg' % i)
        self.assertEqual(len(p), backdrops.LIMIT)
        self.assertEqual(p[0], '59.jpg')

    def test_pick_avoids_current(self):
        rng = random.Random(1)
        for _ in range(20):
            self.assertEqual(backdrops.pick(['a', 'b'], 'a', rng), 'b')
        self.assertEqual(backdrops.pick(['a'], 'a', rng), 'a')
        self.assertEqual(backdrops.pick([], '', rng), '')


if __name__ == '__main__':
    unittest.main()
