import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib.similar import artists_path, genres_of, rank, tracks_path


def artist(ident, name, *genres):
    return {'artistid': ident, 'label': name, 'songgenres': [{'genreid': i, 'title': g} for i, g in enumerate(genres)], 'genre': []}


LIBRARY = [artist(1, 'Dance Punk Band', 'Rock', 'Dance-Punk', 'Electronic'),
           artist(2, 'Other Dance Punk', 'Rock', 'Dance-Punk'),
           artist(3, 'Plain Rock A', 'Rock'),
           artist(4, 'Plain Rock B', 'Rock'),
           artist(5, 'Jazz Man', 'Jazz', ''),
           artist(6, 'Electronic Act', 'Electronic', 'House'),
           artist(7, 'No Genres')]


class Similar(unittest.TestCase):
    def test_genres_lowercased_and_blank_dropped(self):
        self.assertEqual(genres_of({'songgenres': [{'title': 'Rock'}, {'title': ''}, {'title': ' '}], 'genre': ['Pop']}), {'rock', 'pop'})

    def test_cached_entry(self):
        self.assertEqual(genres_of({'artistid': 1, 'label': 'A', 'genres': ['rock', '', 'Pop']}), {'rock', 'pop'})
        cached = [{'artistid': a['artistid'], 'label': a['label'], 'genres': sorted(genres_of(a))} for a in LIBRARY]
        self.assertEqual(rank(cached, 1), rank(LIBRARY, 1))

    def test_rare_shared_genre_ranks_first(self):
        self.assertEqual(rank(LIBRARY, 1)[0], 'Other Dance Punk')

    def test_unrelated_and_self_left_out(self):
        got = rank(LIBRARY, 1)
        self.assertNotIn('Jazz Man', got)
        self.assertNotIn('Dance Punk Band', got)
        self.assertNotIn('No Genres', got)

    def test_blank_genre_matches_nobody(self):
        self.assertEqual(rank(LIBRARY, 5), [])

    def test_count(self):
        self.assertEqual(len(rank(LIBRARY, 1, count=2)), 2)

    def test_unknown_artist_or_no_genres(self):
        self.assertEqual(rank(LIBRARY, 99), [])
        self.assertEqual(rank(LIBRARY, 7), [])
        self.assertEqual(rank([], 1), [])

    def test_genre_everybody_has_does_not_count(self):
        everyone = [artist(i, 'A%d' % i, 'Rock') for i in range(1, 5)]
        self.assertEqual(rank(everyone, 1), [])

    def test_paths(self):
        self.assertEqual(artists_path([]), '')
        path = artists_path(['Simon & Garfunkel', 'AC/DC', 'Guns N\' "Roses"'])
        self.assertTrue(path.startswith('musicdb://artists/?albumartistsonly=false&xsp=%7B'))
        tail = path.split('xsp=')[1]
        self.assertNotIn('&', tail)
        self.assertNotIn('"', tail)
        self.assertNotIn(' ', tail)
        self.assertEqual(tracks_path(23), 'musicdb://songs/?artistid=23')


if __name__ == '__main__':
    unittest.main()
