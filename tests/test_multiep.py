# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib import multiep as m

D = u'–'


def ep(n, title, f, season=6, plot='', runtime=0, duration=0):
    return {'season': season, 'episode': n, 'title': title, 'file': f, 'plot': plot, 'runtime': runtime,
            'streamdetails': {'video': [{'duration': duration}] if duration else []}}


class Paths(unittest.TestCase):
    def test_season_path(self):
        self.assertEqual(m.season_path('videodb://tvshows/titles/1344/6/'), (1344, 6))
        self.assertEqual(m.season_path('videodb://tvshows/titles/1344/-1/?tvshowid=1344'), (1344, -1))
        self.assertIsNone(m.season_path('videodb://tvshows/titles/1344/'))
        self.assertIsNone(m.season_path('videodb://movies/titles/'))
        self.assertIsNone(m.season_path(None))


class Groups(unittest.TestCase):
    def test_lost(self):
        eps = [ep(2, 'LA X (1)', 'a'), ep(1, 'LA X (1)', 'a'), ep(3, 'What Kate Does', 'b'), ep(17, 'The End (1)', 'z'), ep(18, 'The End (2)', 'z')]
        g = m.groups(eps)
        self.assertEqual([[e['episode'] for e in x] for x in g], [[1, 2], [3], [17, 18]])
        self.assertTrue(m.shared(eps))
        self.assertFalse(m.shared([ep(1, 'a', 'x'), ep(2, 'b', 'y'), ep(3, 'c', '')]))

    def test_no_file_stays_alone(self):
        g = m.groups([ep(1, 'a', ''), ep(2, 'b', '')])
        self.assertEqual(len(g), 2)


class Join(unittest.TestCase):
    def test_titles(self):
        self.assertEqual(m.join_title([ep(1, 'LA X (1)', 'a'), ep(2, 'LA X (1)', 'a')]), 'LA X')
        self.assertEqual(m.join_title([ep(17, 'The End (1)', 'a'), ep(18, 'The End (2)', 'a')]), 'The End')
        self.assertEqual(m.join_title([ep(1, 'Pilot, Part 1', 'a'), ep(2, 'Pilot, Part 2', 'a')]), 'Pilot')
        self.assertEqual(m.join_title([ep(1, 'Daffuccino', 'a')] * 3), 'Daffuccino')
        self.assertEqual(m.join_title([ep(1, 'Hare', 'a'), ep(2, 'Duck', 'a'), ep(3, 'Hare', 'a')]), 'Hare / Duck')
        self.assertEqual(m.strip_part('Part 2'), 'Part 2')            # nothing but the marker: kept
        self.assertEqual(m.strip_part('The Departed'), 'The Departed')

    def test_plots(self):
        self.assertEqual(m.join_plot([ep(1, '', '', plot='Same.'), ep(2, '', '', plot='Same.')]), 'Same.')
        self.assertEqual(m.join_plot([ep(1, '', '', plot='Short.'), ep(2, '', '', plot='Short. And more.')]), 'Short. And more.')
        self.assertEqual(m.join_plot([ep(1, '', '', plot='One.'), ep(2, '', '', plot='Two.')]), 'One.\n\nTwo.')

    def test_label(self):
        self.assertEqual(m.label([ep(1, '', '')], 'LA X (1)'), '01. LA X (1)')
        self.assertEqual(m.label([ep(2, '', ''), ep(1, '', '')], 'LA X'), '01' + D + '02. LA X')
        self.assertEqual(m.label([ep(36, '', ''), ep(37, '', ''), ep(38, '', '')], 'Daffuccino'), '36' + D + '38. Daffuccino')
        self.assertEqual(m.label([ep(1, '', ''), ep(3, '', '')], 'A'), '01, 03. A')

    def test_numbers(self):
        self.assertEqual(m.numbers([ep(1, '', '')]), '1')
        self.assertEqual(m.numbers([ep(2, '', ''), ep(1, '', '')]), '1' + D + '2')
        self.assertEqual(m.numbers([ep(36, '', ''), ep(37, '', ''), ep(38, '', '')]), '36' + D + '38')
        self.assertEqual(m.numbers([ep(1, '', ''), ep(3, '', '')]), '1, 3')

    def test_runtime_file_first(self):
        # every part carries the whole file's length: the file's duration once, not the sum
        self.assertEqual(m.runtime([ep(17, '', '', runtime=6283, duration=6283), ep(18, '', '', runtime=6283, duration=6283)]), 6283)
        self.assertEqual(m.runtime([ep(36, '', '', runtime=727, duration=727)] * 3), 727)
        # no file duration known: the parts' running times added up
        self.assertEqual(m.runtime([ep(1, '', '', runtime=1260), ep(2, '', '', runtime=1320)]), 2580)

    def test_codes(self):
        parts = [ep(1, '', ''), ep(2, '', '')]
        self.assertEqual(m.code(parts, ''), '6x01' + D + '02')
        self.assertEqual(m.code(parts, 'sxe'), 'S06E01' + D + 'E02')
        self.assertEqual(m.code(parts, 'sp'), 'S6 E1' + D + '2')
        self.assertEqual(m.code(parts, 'bar'), 'S6 | E1' + D + '2')
        self.assertEqual(m.code(parts, 'dot'), u'S6 • E1' + D + '2')
        self.assertEqual(m.code([ep(36, '', '', season=1), ep(37, '', '', season=1), ep(38, '', '', season=1)], ''), '1x36' + D + '38')
        self.assertEqual(m.code([ep(1, '', ''), ep(3, '', '')], 'sxe'), 'S06E01, E03')


if __name__ == '__main__':
    unittest.main()
