# -*- coding: utf-8 -*-
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
for name in ('xbmc', 'xbmcgui'):
    sys.modules.setdefault(name, types.ModuleType(name))
import focusart  # noqa: E402


class TestFocusArt(unittest.TestCase):
    def test_request(self):
        self.assertEqual(focusart.request('movie', '42'), ('VideoLibrary.GetMovieDetails', {'movieid': 42, 'properties': ['art']}, 'moviedetails'))
        self.assertEqual(focusart.request('set', '7')[0], 'VideoLibrary.GetMovieSetDetails')
        self.assertEqual(focusart.request('album', '3')[1], {'albumid': 3, 'properties': ['art']})
        for bad in (('movie', ''), ('movie', '-1'), ('movie', '0'), ('song', '5'), ('', '5'), ('movie', 'x')):
            self.assertIsNone(focusart.request(*bad), bad)

    def test_pick(self):
        film = {'poster': 'p', 'fanart': 'f', 'clearlogo': 'l', 'landscape': 'w'}
        self.assertEqual(focusart.pick('movie', film), {'poster': 'p', 'fanart': 'f', 'thumb': 'p', 'landscape': 'w', 'clearlogo': 'l'})
        episode = {'thumb': 't', 'season.poster': 'sp', 'tvshow.poster': 'tp', 'tvshow.fanart': 'tf', 'tvshow.clearlogo': 'tl'}
        self.assertEqual(focusart.pick('episode', episode), {'poster': 'sp', 'fanart': 'tf', 'thumb': 't', 'landscape': '', 'clearlogo': 'tl'})
        self.assertEqual(focusart.pick('season', {'tvshow.poster': 'tp'})['poster'], 'tp')
        self.assertEqual(focusart.pick('artist', {'thumb': 'a', 'fanart': 'f'}), {'poster': '', 'fanart': 'f', 'thumb': 'a', 'landscape': '', 'clearlogo': ''})
        self.assertEqual(focusart.pick('movie', None), dict((k, '') for k in focusart.KINDS))


if __name__ == '__main__':
    unittest.main()
