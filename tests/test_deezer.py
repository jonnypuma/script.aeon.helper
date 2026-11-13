# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib.deezer import find_artist, lookup, match_artists, match_tracks, norm, related, top_tracks

SEARCH = {'data': [{'id': 9, 'name': 'Daft Punk Experience', 'nb_fan': 64},
                   {'id': 412, 'name': 'Daft Punk', 'nb_fan': 0},
                   {'id': 27, 'name': 'daft punk', 'nb_fan': 5000000}]}
TOP = {'data': [{'title': 'One More Time', 'album': {'title': 'Discovery', 'cover_medium': 'c1'}},
                {'title': 'One More Time (Radio Edit)', 'album': {'title': 'Singles', 'cover_medium': 'c2'}},
                {'title': 'Instant Crush (feat. Julian Casablancas)', 'album': {'title': 'RAM', 'cover_medium': 'c3'}},
                {'title': '', 'album': {}}]}
RELATED = {'data': [{'name': 'Justice', 'picture_medium': 'p1'}, {'name': 'The Chemical Brothers', 'picture_medium': 'p2'}, {'name': ''}]}


def fetch(url):
    if '/search/artist' in url:
        return SEARCH
    if '/top' in url:
        return TOP
    if '/related' in url:
        return RELATED
    return None


class Deezer(unittest.TestCase):
    def test_norm(self):
        self.assertEqual(norm('The Chemical Brothers'), 'chemical brothers')
        self.assertEqual(norm(u'Beyoncé'), 'beyonce')
        self.assertEqual(norm('Instant Crush (feat. Julian Casablancas)'), 'instant crush')
        self.assertEqual(norm('Get Lucky feat. Pharrell Williams'), 'get lucky')
        self.assertEqual(norm('Simon & Garfunkel'), norm('Simon and Garfunkel'))
        self.assertEqual(norm("Don't Stop [Remastered]"), 'don t stop')
        self.assertEqual(norm(None), '')

    def test_find_artist_exact_name_most_fans(self):
        self.assertEqual(find_artist(fetch, 'Daft Punk'), 27)

    def test_find_artist_unknown(self):
        self.assertIsNone(find_artist(fetch, 'Nobody At All'))
        self.assertIsNone(find_artist(fetch, ''))
        self.assertIsNone(find_artist(lambda url: None, 'Daft Punk'))

    def test_search_url_is_encoded(self):
        seen = []
        find_artist(lambda url: seen.append(url) or SEARCH, u'Simon & Garfunkel é')
        self.assertIn('q=Simon%20%26%20Garfunkel%20%C3%A9', seen[0])

    def test_top_tracks_drop_doubles_and_blanks(self):
        got = top_tracks(fetch, 27)
        self.assertEqual([t['title'] for t in got], ['One More Time', 'Instant Crush (feat. Julian Casablancas)'])
        self.assertEqual(got[0], {'title': 'One More Time', 'album': 'Discovery', 'cover': 'c1'})

    def test_related(self):
        self.assertEqual(related(fetch, 27), [{'name': 'Justice', 'picture': 'p1'}, {'name': 'The Chemical Brothers', 'picture': 'p2'}])

    def test_lookup(self):
        got = lookup(fetch, 'Daft Punk')
        self.assertEqual(len(got['tracks']), 2)
        self.assertEqual(len(got['related']), 2)
        self.assertIsNone(lookup(fetch, 'Nobody At All'))

    def test_match_tracks(self):
        songs = [{'songid': 1, 'title': 'Instant Crush', 'playcount': 0}, {'songid': 2, 'title': 'One more time', 'playcount': 1},
                 {'songid': 3, 'title': 'One More Time (Live)', 'playcount': 7}, {'songid': 4, 'title': 'Aerodynamic'}]
        pairs = match_tracks(top_tracks(fetch, 27), songs)
        self.assertEqual([song and song['songid'] for _track, song in pairs], [2, 1])       # same title beats the live cut
        live_only = [{'songid': 3, 'title': 'One More Time (Live)', 'playcount': 7}, {'songid': 5, 'title': 'One More Time (Edit)', 'playcount': 9}]
        self.assertEqual(match_tracks(top_tracks(fetch, 27), live_only)[0][1]['songid'], 5)    # no exact title: most played
        self.assertEqual(match_tracks(top_tracks(fetch, 27), [])[0][1], None)

    def test_match_artists(self):
        library = [{'artistid': 5, 'label': 'Chemical Brothers'}, {'artistid': 6, 'label': 'Air'}]
        pairs = match_artists(related(fetch, 27), library)
        self.assertEqual([(entry['name'], artist and artist['artistid']) for entry, artist in pairs], [('Justice', None), ('The Chemical Brothers', 5)])


if __name__ == '__main__':
    unittest.main()
