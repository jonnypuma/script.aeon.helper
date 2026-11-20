import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib import online
from resources.lib.online import build_path, find, index, plain, year_of

LIBRARY = [{'movieid': 1, 'title': 'The Creator', 'year': 2023, 'uniqueid': {'tmdb': '670292', 'imdb': 'tt1'}},
           {'movieid': 2, 'title': u'Amélie', 'year': 2001, 'uniqueid': {}},
           {'movieid': 3, 'title': 'Solaris', 'year': 1972, 'uniqueid': {'tmdb': '593'}},
           {'movieid': 0, 'title': 'Broken'}]


class Online(unittest.TestCase):
    def setUp(self):
        self.by_tmdb, self.by_title = index(LIBRARY, 'movieid')

    def test_match_by_tmdb_id(self):
        self.assertEqual(find({'label': 'Creator, The', 'uniqueid': {'tmdb': 670292}}, self.by_tmdb, self.by_title), 1)

    def test_other_id_is_another_film_even_with_same_title(self):
        self.assertIsNone(find({'label': 'Solaris', 'year': 2002, 'uniqueid': {'tmdb': '2103'}}, self.by_tmdb, self.by_title))

    def test_library_item_without_tmdb_id_matches_entry_that_has_one(self):
        self.assertEqual(find({'label': 'Amelie', 'year': 2001, 'uniqueid': {'tmdb': '194'}}, self.by_tmdb, self.by_title), 2)

    def test_match_by_title_and_year_without_id(self):
        self.assertEqual(find({'label': 'Amelie', 'premiered': '2001-04-25'}, self.by_tmdb, self.by_title), 2)
        self.assertIsNone(find({'label': 'Amelie', 'year': 1999}, self.by_tmdb, self.by_title))

    def test_markup_is_ignored(self):
        self.assertEqual(plain('[COLOR=ffcc0000][I]Ghost Soldier[/I][/COLOR]'), 'Ghost Soldier')
        self.assertEqual(find({'label': '[COLOR=ffcc0000][I]Amelie[/I][/COLOR]', 'year': 2001}, self.by_tmdb, self.by_title), 2)

    def test_year_of(self):
        self.assertEqual(year_of({'year': 1968}), 1968)
        self.assertEqual(year_of({'firstaired': '2008-01-20'}), 2008)
        self.assertEqual(year_of({}), 0)

    def test_items_without_id_skipped(self):
        self.assertNotIn(0, self.by_title.values())

    def test_build_path(self):
        self.assertEqual(build_path('upcoming', 'movie'), 'plugin://plugin.video.themoviedb.helper/?info=upcoming&tmdb_type=movie')
        self.assertEqual(build_path('similar', 'tv', 'Breaking Bad'), 'plugin://plugin.video.themoviedb.helper/?info=similar&tmdb_type=tv&query=Breaking Bad')
        self.assertEqual(build_path('recommendations', 'movie', 'Alien', '1979'), 'plugin://plugin.video.themoviedb.helper/?info=recommendations&tmdb_type=movie&query=Alien&year=1979')
        self.assertIsNone(build_path('similar', 'movie'))
        self.assertIsNone(build_path('play', 'movie'))
        self.assertIsNone(build_path('popular', 'person'))


if __name__ == '__main__':
    unittest.main()


def test_origin_of():
    assert online.origin_of('') == ''
    assert online.origin_of('us') == 'US'
    assert online.origin_of('NO') == 'US%7CNO'
    assert online.origin_of('Norway') == ''


def test_cinema_path_with_origin():
    plain = online.build_path('now_playing', 'movie')
    assert plain == 'plugin://plugin.video.themoviedb.helper/?info=now_playing&tmdb_type=movie'
    kept = online.build_path('now_playing', 'movie', origin='US%7CGB')
    assert kept.startswith('plugin://plugin.video.themoviedb.helper/?info=discover&tmdb_type=movie')
    assert kept.endswith('&with_origin_country=US%7CGB') and 'release_date.gte=t-42' in kept
    assert online.build_path('popular', 'movie', origin='US') == 'plugin://plugin.video.themoviedb.helper/?info=popular&tmdb_type=movie'
    assert online.build_path('now_playing', 'tv', origin='US') == 'plugin://plugin.video.themoviedb.helper/?info=now_playing&tmdb_type=tv'


def test_cinema_countries_are_codes():
    codes = [code for _, code in online.CINEMA_COUNTRIES]
    assert len(codes) == len(set(codes)) and all(len(c) == 2 and c.isupper() for c in codes) and 'US' not in codes
