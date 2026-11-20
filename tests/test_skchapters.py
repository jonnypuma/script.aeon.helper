# -*- coding: utf-8 -*-
"""0.3.112: Skippy's segments as chapters on the player's bar (resources/lib/skchapters.py, pure parts)"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import skchapters as sk  # noqa: E402

# the box, 2026-11-18: an episode without chapters, 58:10, segments from TheIntroDB / IntroDB
SEGS = [{'start': 1.0, 'end': 38.105, 'label': 'recap'}, {'start': 643.999, 'end': 733.722, 'label': 'intro'},
        {'start': 3197.57, 'end': 3489.76, 'label': 'credits'}]
TOTAL = 3490.0


class BoundariesTest(unittest.TestCase):
    def test_episode(self):
        # 1.0 is at the start, 3489.76 at the end: both dropped
        self.assertEqual(sk.boundaries(SEGS, TOTAL), [38.105, 643.999, 733.722, 3197.57])

    def test_near_cuts_merge(self):
        segs = [{'start': 100.0, 'end': 200.0}, {'start': 205.0, 'end': 400.0}]
        self.assertEqual(sk.boundaries(segs, 1000.0), [100.0, 200.0, 400.0])

    def test_nested(self):
        segs = [{'start': 5.0, 'end': 70.0}, {'start': 25.0, 'end': 40.0}]
        self.assertEqual(sk.boundaries(segs, 1000.0), [25.0, 40.0, 70.0])

    def test_bad_input(self):
        self.assertEqual(sk.boundaries(SEGS, 0), [])
        self.assertEqual(sk.boundaries(SEGS, None), [])
        self.assertEqual(sk.boundaries([{'start': 'x'}, None, {'end': True}], 100.0), [])


class RangesTest(unittest.TestCase):
    def test_pairs(self):
        self.assertEqual(sk.ranges([25.0, 50.0], 100.0), '0.00000,25.00000,25.00000,50.00000,50.00000,100.00000')

    def test_none(self):
        self.assertEqual(sk.ranges([], 100.0), '')

    def test_episode_count(self):
        values = sk.ranges(sk.boundaries(SEGS, TOTAL), TOTAL).split(',')
        self.assertEqual(len(values), 10)            # five chapters
        self.assertEqual(values[-1], '100.00000')


class PartTest(unittest.TestCase):
    def test_parts(self):
        cuts = [38.105, 643.999, 733.722, 3197.57]
        self.assertEqual(sk.part(cuts, 0), 1)
        self.assertEqual(sk.part(cuts, 700), 3)
        self.assertEqual(sk.part(cuts, 3197.57), 5)


class ParseTest(unittest.TestCase):
    def snap(self, path):
        return json.dumps({'v': 1, 'path': path, 'segments': SEGS})

    def test_same_file(self):
        self.assertEqual(sk.parse(self.snap('/media/show/e01.mkv'), '/media/show/e01.mkv'), SEGS)

    def test_quoted(self):
        self.assertEqual(sk.parse(self.snap('/media/a%20b.mkv'), '/media/a b.mkv'), SEGS)

    def test_other_file(self):
        self.assertEqual(sk.parse(self.snap('/media/show/e01.mkv'), '/media/show/e02.mkv'), [])

    def test_bad(self):
        self.assertEqual(sk.parse('', 'x'), [])
        self.assertEqual(sk.parse('{nope', 'x'), [])
        self.assertEqual(sk.parse(json.dumps({'v': 2, 'path': 'x', 'segments': SEGS}), 'x'), [])


if __name__ == '__main__':
    unittest.main()
