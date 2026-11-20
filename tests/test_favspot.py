# -*- coding: utf-8 -*-
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib import favspot

WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
          'November', 'December']


def ep(season, number, playcount=0, position=0, lastplayed=''):
    return {'season': season, 'episode': number, 'playcount': playcount, 'resume': {'position': position, 'total': 3600},
            'lastplayed': lastplayed, 'runtime': 3600}


class Shape(unittest.TestCase):
    def test_shapes(self):
        self.assertEqual(favspot.shape('tvshow'), 'wide')
        self.assertEqual(favspot.shape('movie'), 'poster')
        self.assertEqual(favspot.shape('album'), 'square')
        self.assertEqual(favspot.shape('channel'), 'square')

    def test_art(self):
        art = {'landscape': 'l', 'fanart': 'f', 'poster': 'p', 'thumb': 't'}
        self.assertEqual(favspot.tile_art('tvshow', art), 'l')
        self.assertEqual(favspot.tile_art('tvshow', {'fanart': 'f'}), 'f')
        self.assertEqual(favspot.tile_art('movie', art), 'p')
        self.assertEqual(favspot.tile_art('album', {'thumb': 't'}), 't')
        self.assertEqual(favspot.tile_art('channel', {}, 'logo.png'), 'logo.png')
        self.assertEqual(favspot.shape('episode'), 'wide')
        self.assertEqual(favspot.tile_art('episode', {'thumb': 'e', 'landscape': 'l'}), 'e')
        self.assertEqual(favspot.tile_art('episode', {'landscape': 'l'}), 'l')

    def test_playlist(self):
        self.assertTrue(favspot.is_playlist('special://profile/playlists/music/x.xsp'))
        self.assertFalse(favspot.is_playlist('videodb://movies/'))


class Continue(unittest.TestCase):
    def test_part_watched_wins(self):
        eps = [ep(3, 1, position=1300, lastplayed='2026-11-10'), ep(3, 2), ep(3, 3), ep(3, 4), ep(2, 8, 1)]
        chosen, started, more = favspot.continue_episode(eps)
        self.assertEqual((chosen['season'], chosen['episode'], started, more), (3, 1, True, 3))

    def test_first_unwatched(self):
        eps = [ep(1, 1, 1), ep(1, 2, 1), ep(1, 3), ep(2, 1), ep(0, 1)]
        chosen, started, more = favspot.continue_episode(eps)
        self.assertEqual((chosen['season'], chosen['episode'], started, more), (1, 3, False, 0))

    def test_specials_last(self):
        chosen, _started, _more = favspot.continue_episode([ep(0, 1), ep(1, 1)])
        self.assertEqual(chosen['season'], 1)

    def test_all_watched(self):
        self.assertEqual(favspot.continue_episode([ep(1, 1, 1)]), (None, False, 0))
        self.assertEqual(favspot.continue_episode([]), (None, False, 0))

    def test_progress(self):
        self.assertEqual(favspot.progress({'resume': {'position': 1320, 'total': 3600}}), (37, 38))
        self.assertEqual(favspot.progress({'resume': {'position': 0, 'total': 0}, 'runtime': 2700}), (0, 45))
        self.assertEqual(favspot.progress({}), (0, 0))


class Airing(unittest.TestCase):
    def test_next(self):
        today = datetime.date(2026, 11, 14)
        entries = [{'showtitle': 'The Rings of Power', 'season': 3, 'episode': 6, 'premiered': '2026-11-25'},
                   {'showtitle': 'The Rings of Power', 'season': 3, 'episode': 5, 'premiered': '2026-11-18'},
                   {'showtitle': 'The Rings of Power', 'season': 3, 'episode': 4, 'premiered': '2026-11-11'},
                   {'showtitle': 'Other', 'season': 1, 'episode': 1, 'premiered': '2026-11-15'}]
        found = favspot.next_airing(entries, 'the rings of power', today)
        self.assertEqual((found['season'], found['episode']), (3, 5))
        self.assertIsNone(favspot.next_airing(entries, 'Nothing', today))

    def test_date(self):
        today = datetime.date(2026, 11, 14)
        self.assertEqual(favspot.air_date('2026-11-18', today, WEEKDAYS, MONTHS), 'Wednesday 18 November')
        self.assertEqual(favspot.air_date('2026-11-15', today, WEEKDAYS, MONTHS, {'tomorrow': 'Tomorrow'}), 'Tomorrow 15 November')
        self.assertEqual(favspot.air_date('x', today, WEEKDAYS, MONTHS), '')

    def test_fill(self):
        self.assertEqual(favspot.fill('{n} min left', n=38), '38 min left')
        self.assertEqual(favspot.fill('{episode} airs {date}', episode='S3 E5', date='Wednesday'), 'S3 E5 airs Wednesday')
        self.assertEqual(favspot.fill('broken {x}', n=1), 'broken {x}')


if __name__ == '__main__':
    unittest.main()
