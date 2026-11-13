# -*- coding: utf-8 -*-
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import arr

TODAY = datetime.date(2026, 11, 13)

FILM = {'title': 'Avatar: Fire and Ash', 'year': 2025, 'monitored': True, 'hasFile': False, 'runtime': 190,
        'inCinemas': '2026-12-18T00:00:00Z', 'digitalRelease': '2027-03-01T00:00:00Z', 'physicalRelease': '2026-12-30T00:00:00Z',
        'overview': 'Pandora.', 'genres': ['Science Fiction'], 'certification': 'PG-13', 'studio': '20th Century',
        'ratings': {'tmdb': {'value': 7.6, 'votes': 900}},
        'images': [{'coverType': 'poster', 'remoteUrl': 'https://image.tmdb.org/p.jpg', 'url': '/MediaCover/1/poster.jpg?apikey=x'},
                   {'coverType': 'fanart', 'remoteUrl': 'https://image.tmdb.org/f.jpg'}]}
NOW = {'title': 'Wicked: For Good', 'monitored': True, 'hasFile': False, 'inCinemas': '2026-10-30T00:00:00Z',
       'digitalRelease': '2026-12-20T00:00:00Z'}
HAVE = dict(FILM, title='Got it', hasFile=True)
EPISODE = {'title': 'Shadow and Flame', 'seasonNumber': 3, 'episodeNumber': 5, 'airDate': '2026-11-18', 'hasFile': False,
           'monitored': True, 'overview': 'Battle.',
           'series': {'title': 'The Rings of Power', 'network': 'Prime Video', 'runtime': 70, 'genres': ['Fantasy'],
                      'images': [{'coverType': 'poster', 'remoteUrl': 'https://artworks.thetvdb.com/p.jpg'}]}}
NEWSHOW = dict(EPISODE, series={'title': 'Brand New Show', 'images': []}, seasonNumber=1, episodeNumber=1)
ALBUM = {'title': 'Midnights II', 'releaseDate': '2026-11-20T00:00:00Z', 'monitored': True, 'statistics': {'trackFileCount': 0},
         'images': [{'coverType': 'cover', 'remoteUrl': 'https://coverartarchive.org/c.jpg'}],
         'artist': {'artistName': 'Taylor Swift', 'images': [{'coverType': 'fanart', 'remoteUrl': 'https://fanart.tv/a.jpg'}]}}


class TestArr(unittest.TestCase):
    def test_radarr_dates(self):
        got = arr.radarr_entries([FILM, HAVE], TODAY, 60)
        self.assertEqual([(e['release'], e['premiered']) for e in got], [('cinema', '2026-12-18'), ('physical', '2026-12-30')])
        self.assertEqual(got[0]['art'], {'poster': 'https://image.tmdb.org/p.jpg', 'fanart': 'https://image.tmdb.org/f.jpg'})
        self.assertEqual(got[0]['more']['rating'], 7.6)
        self.assertEqual(got[0]['runtime'], 190 * 60)

    def test_radarr_in_cinemas_now(self):
        got = arr.radarr_entries([NOW], TODAY, 60)
        self.assertEqual([(e['release'], e['premiered']) for e in got], [('cinemanow', '2026-11-13'), ('digital', '2026-12-20')])
        past_digital = dict(NOW, digitalRelease='2026-11-01T00:00:00Z')
        self.assertEqual(arr.radarr_entries([past_digital], TODAY, 60), [])

    def test_sonarr(self):
        got = arr.sonarr_entries([EPISODE, NEWSHOW, dict(EPISODE, hasFile=True)], TODAY, 30, ['The Rings of Power'])
        self.assertEqual([(e['release'], e['showtitle'], e['season'], e['episode']) for e in got],
                         [('episode', 'The Rings of Power', 3, 5), ('newshow', 'Brand New Show', 1, 1)])
        self.assertEqual(got[0]['art']['tvshow.poster'], 'https://artworks.thetvdb.com/p.jpg')
        self.assertEqual(arr.sonarr_entries([EPISODE], TODAY, 2), [])          # past the window

    def test_lidarr(self):
        got = arr.lidarr_entries([ALBUM, dict(ALBUM, statistics={'trackFileCount': 3})], TODAY, 30)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]['artist'], 'Taylor Swift')
        self.assertEqual(got[0]['art']['thumb'], 'https://coverartarchive.org/c.jpg')
        self.assertEqual(got[0]['art']['fanart'], 'https://fanart.tv/a.jpg')

    def test_combine_and_pick(self):
        base = [{'kind': 'episode', 'showtitle': 'The Rings of Power', 'season': 3, 'episode': 5, 'premiered': '2026-11-18'},
                {'kind': 'movie', 'title': 'Avatar: Fire and Ash', 'premiered': '2026-12-18'}]
        wanted = arr.sonarr_entries([EPISODE], TODAY, 30) + arr.radarr_entries([FILM], TODAY, 60) + arr.lidarr_entries([ALBUM], TODAY, 30)
        got = arr.combine(base, wanted)
        self.assertEqual(sum(1 for e in got if e['kind'] == 'episode'), 1)            # not twice
        films = [e for e in got if e['kind'] == 'movie']
        self.assertTrue(all(e.get('source') == 'radarr' for e in films))              # the app's entry wins
        self.assertEqual(len(arr.pick(got, 'films')), 2)
        self.assertEqual(sorted(e['kind'] for e in arr.pick(got, 'episodes')), ['album', 'episode'])

    def test_no_local_image_urls(self):
        self.assertNotIn('apikey', str(arr.radarr_entries([FILM], TODAY, 60)))


if __name__ == '__main__':
    unittest.main()
