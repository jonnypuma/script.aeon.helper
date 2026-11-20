# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import planner


class TestEpisodeKind(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(planner.episode_kind(1, 1), 'series_premiere')
        self.assertEqual(planner.episode_kind(3, 1, 'standard'), 'season_premiere')
        self.assertEqual(planner.episode_kind(2, 10, 'season_finale', 'Returning Series'), 'season_finale')
        self.assertEqual(planner.episode_kind(2, 10, 'finale', 'Ended'), 'series_finale')
        self.assertEqual(planner.episode_kind(5, 16, 'season_finale', 'Canceled'), 'series_finale')
        self.assertEqual(planner.episode_kind(2, 5, 'mid_season_finale'), 'mid_season_finale')
        self.assertEqual(planner.episode_kind(2, 5, 'standard'), '')
        self.assertEqual(planner.episode_kind(0, 3, 'special'), '')
        self.assertEqual(planner.episode_kind('x', 3), '')
        self.assertIn('season_finale', planner.EPKIND_WORDS)


if __name__ == '__main__':
    unittest.main()


def test_entry_kind_old_list_premieres():
    # a Planner list kept from before 0.3.97 has no 'epkind': the premieres come from the numbers
    assert planner.entry_kind({'season': 3, 'episode': 1}) == 'season_premiere'
    assert planner.entry_kind({'season': 1, 'episode': 1}) == 'series_premiere'
    assert planner.entry_kind({'season': 2, 'episode': 4}) == ''
    assert planner.entry_kind({'kind': 'movie', 'season': 0, 'episode': 0}) == ''


def test_entry_kind_new_list_wins():
    assert planner.entry_kind({'season': 4, 'episode': 8, 'epkind': 'season_finale'}) == 'season_finale'
    assert planner.entry_kind({'season': 3, 'episode': 1, 'epkind': ''}) == ''
