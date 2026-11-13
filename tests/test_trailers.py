import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib.trailers import is_trailer, pick

MOVIE = ['A.Quiet.Place.2020.REMUX.mkv', 'A.Quiet.Place.2020.REMUX-trailer.mkv', 'A.Quiet.Place.2020.REMUX-poster.jpg',
         'A.Quiet.Place.2020.REMUX-trailer.trickplay', 'fanart.jpg', 'extrafanart']
SHOW = ['tvshow.nfo', 'tvshow-trailer.mp4', 'tvshow-trailer.trickplay', 'season01-trailer.mkv', 'Season 1', 'poster.jpg']


class Trailers(unittest.TestCase):
    def test_is_trailer(self):
        self.assertTrue(is_trailer('Film-trailer.mkv'))
        self.assertTrue(is_trailer('trailer.MP4'))
        self.assertTrue(is_trailer('tvshow-trailer.mp4'))
        self.assertFalse(is_trailer('tvshow-trailer.trickplay'))      # a folder of preview images
        self.assertFalse(is_trailer('Film-trailer.jpg'))
        self.assertFalse(is_trailer('Trailer Park Boys.mkv'))
        self.assertFalse(is_trailer('Supertrailer.mkv'))

    def test_movie_own_sidecar(self):
        self.assertEqual(pick(MOVIE, 'movie', 'A.Quiet.Place.2020.REMUX'), 'A.Quiet.Place.2020.REMUX-trailer.mkv')

    def test_movie_generic_and_single(self):
        self.assertEqual(pick(['film.mkv', 'movie-trailer.mp4', 'other-trailer.mkv'], 'movie', 'film'), 'movie-trailer.mp4')
        self.assertEqual(pick(['film.mkv', 'something-trailer.mkv'], 'movie', 'film'), 'something-trailer.mkv')

    def test_movie_two_films_in_one_folder(self):
        names = ['a.mkv', 'a-trailer.mkv', 'b.mkv', 'b-trailer.mkv']
        self.assertEqual(pick(names, 'movie', 'b'), 'b-trailer.mkv')
        self.assertEqual(pick(names, 'movie', 'c'), '')                # not somebody else's trailer

    def test_show_and_season(self):
        self.assertEqual(pick(SHOW, 'tvshow'), 'tvshow-trailer.mp4')
        self.assertEqual(pick(SHOW, 'season', season=1), 'season01-trailer.mkv')
        self.assertEqual(pick(SHOW, 'season', season='2'), 'tvshow-trailer.mp4')
        self.assertEqual(pick(['season01-trailer.mkv'], 'tvshow'), '')

    def test_episode(self):
        self.assertEqual(pick(['s01e01.mkv', 's01e01-trailer.mkv', 'tvshow-trailer.mp4'], 'episode', 's01e01'), 's01e01-trailer.mkv')
        self.assertEqual(pick(['s01e02.mkv', 'tvshow-trailer.mp4'], 'episode', 's01e02'), '')

    def test_nothing(self):
        self.assertEqual(pick([], 'movie', 'x'), '')
        self.assertEqual(pick(None, 'tvshow'), '')
        self.assertEqual(pick(['film.mkv', 'poster.jpg'], 'movie', 'film'), '')


if __name__ == '__main__':
    unittest.main()
