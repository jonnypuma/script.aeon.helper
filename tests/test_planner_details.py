import datetime
# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import planner


class TestPlannerDetails(unittest.TestCase):
    def test_cast_list(self):
        raw = [{'name': 'A', 'role': 'X', 'thumbnail': 't'}, {'name': 'A', 'role': 'again'}, {'name': ''}, 'junk', {'name': 'B'}]
        self.assertEqual(planner.cast_list(raw), [{'name': 'A', 'role': 'X', 'thumbnail': 't'}, {'name': 'B', 'role': '', 'thumbnail': ''}])
        self.assertEqual(len(planner.cast_list([{'name': str(n)} for n in range(30)], limit=5)), 5)
        self.assertEqual(planner.cast_list(None), [])

    def test_details(self):
        entry = {'genre': ['Comedy', ''], 'mpaa': 'Rated TV-MA', 'studio': ['Comedy Central'], 'rating': 7.26, 'votes': '12', 'cast': [{'name': 'A'}]}
        got = planner.details(entry, {'network': 'Comedy Central'})
        self.assertEqual(got['genre'], ['Comedy'])
        self.assertEqual((got['mpaa'], got['studio'], got['rating'], got['votes'], got['network']), ('Rated TV-MA', ['Comedy Central'], 7.3, 12, 'Comedy Central'))
        self.assertEqual(got['cast'][0]['name'], 'A')

    def test_details_of_nothing(self):
        got = planner.details({'rating': 'x', 'votes': None})
        self.assertEqual((got['genre'], got['mpaa'], got['rating'], got['votes'], got['cast'], got['network']), ([], '', 0.0, 0, [], ''))


if __name__ == '__main__':
    unittest.main()


def test_airing_candidates_skip_ended_and_unknown_ids():
    shows = [{'title': 'A', 'status': 'Continuing', 'uniqueid': {'tmdb': '1'}},
             {'title': 'B', 'status': 'Ended', 'uniqueid': {'tmdb': '2'}},
             {'title': 'C', 'status': 'Returning Series', 'uniqueid': {'tmdb': '3'}},
             {'title': 'D', 'status': 'Canceled', 'uniqueid': {'tmdb': '4'}},
             {'title': 'E', 'status': '', 'uniqueid': {'tmdb': '5'}},
             {'title': 'F', 'status': 'Continuing', 'uniqueid': {'imdb': 'tt1'}}]
    assert planner.airing_candidates(shows) == [('A', '1'), ('C', '3'), ('E', '5')]


def test_next_episode_from_details():
    custom = {'next_aired.original': '2026-11-18', 'next_aired.season': '3', 'next_aired.episode': '5',
              'next_aired.title': 'Episode 5', 'next_aired.duration': '3600'}
    entry = {'title': 'The Rings of Power', 'art': {'poster': 'p.jpg', 'fanart': 'f.jpg', 'clearlogo': 'c.png'}}
    ep = planner.next_episode('The Lord of the Rings: The Rings of Power', entry, custom, datetime.date(2026, 11, 13))
    assert ep['season'] == 3 and ep['episode'] == 5 and ep['premiered'] == '2026-11-18' and ep['runtime'] == 3600
    assert ep['title'] == 'Episode 5' and ep['showtitle'] == 'The Lord of the Rings: The Rings of Power'
    assert ep['art']['tvshow.poster'] == 'p.jpg' and ep['art']['thumb'] == 'f.jpg' and ep['art']['clearlogo'] == 'c.png'
    # passed, missing or broken dates: nothing
    assert planner.next_episode('X', entry, dict(custom, **{'next_aired.original': '2026-11-01'}), datetime.date(2026, 11, 13)) is None
    assert planner.next_episode('X', entry, {}, datetime.date(2026, 11, 13)) is None
    assert planner.next_episode('X', entry, dict(custom, **{'next_aired.season': 'x'}), datetime.date(2026, 11, 13)) is None


def test_quiet_enough_waits_three_minutes_after_playback_and_keys():
    now = 10000.0
    assert planner.quiet_enough(now, now - 181, True) is True
    assert planner.quiet_enough(now, now - 179, True) is False      # playback ended under three minutes ago
    assert planner.quiet_enough(now, now - 3600, False) is False    # a key was pressed in the last three minutes
    assert planner.QUIET == 180
