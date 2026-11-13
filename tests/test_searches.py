# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import searches


class TestSearches(unittest.TestCase):
    def test_add_puts_newest_first_without_repeats(self):
        h = searches.add([], 'rings')
        h = searches.add(h, 'godfather')
        h = searches.add(h, '  Rings ')
        self.assertEqual(h, ['Rings', 'godfather'])

    def test_blank_changes_nothing(self):
        self.assertEqual(searches.add(['a'], '   '), ['a'])
        self.assertEqual(searches.add(['a'], None), ['a'])

    def test_limit(self):
        h = []
        for i in range(12):
            h = searches.add(h, 'q%d' % i)
        self.assertEqual(len(h), searches.LIMIT)
        self.assertEqual(h[0], 'q11')
        self.assertEqual(h[-1], 'q4')

    def test_clean_folds_spaces(self):
        self.assertEqual(searches.clean('  tulsa   king '), 'tulsa king')

    def test_remove(self):
        self.assertEqual(searches.remove(['a', 'b', 'c'], 1), ['a', 'c'])
        self.assertEqual(searches.remove(['a'], 5), ['a'])


if __name__ == '__main__':
    unittest.main()
