# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import favourites as fv

SHOW = {'type': 'window', 'title': 'The Rings of Power', 'window': 'videos', 'windowparameter': 'videodb://tvshows/titles/412/'}
FILM = {'type': 'media', 'title': '3 Godfathers', 'path': 'nfs://nas/Movies/3 Godfathers (1948).mkv'}
ALBUM = {'type': 'window', 'title': '21', 'window': 'music', 'windowparameter': 'musicdb://albums/77/'}
CHANNEL = {'type': 'media', 'title': 'Viasat Sport', 'path': 'pvr://channels/tv/All channels/pvr.iptvsimple_7.pvr'}
ADDON = {'type': 'script', 'title': 'Skippy', 'path': 'script.skippy'}
PLUGIN = {'type': 'window', 'title': 'YouTube', 'window': 'videos', 'windowparameter': 'plugin://plugin.video.youtube/'}
SETTINGS = {'type': 'window', 'title': 'Settings', 'window': 'settings'}


class TestFavourites(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(fv.classify(SHOW), ('video', 'tvshow', 412))
        self.assertEqual(fv.classify(FILM), ('video', 'file', 0))
        self.assertEqual(fv.classify(ALBUM), ('music', 'album', 77))
        self.assertEqual(fv.classify(CHANNEL), ('video', 'channel', 0))
        self.assertEqual(fv.classify(ADDON), ('addons', 'addon', 0))
        self.assertEqual(fv.classify(PLUGIN), ('video', 'addon', 0))
        self.assertEqual(fv.classify(SETTINGS), ('other', 'window', 0))

    def test_wanted_keeps_kodi_order_and_index(self):
        favs = [SHOW, ALBUM, FILM, ADDON]
        self.assertEqual([i for i, _ in fv.wanted(favs, 'video')], [0, 2])
        self.assertEqual([i for i, _ in fv.wanted(favs, 'music')], [1])
        self.assertEqual([i for i, _ in fv.wanted(favs, 'all')], [0, 1, 2, 3])
        self.assertEqual(len(fv.wanted(favs, 'nonsense')), 4)

    def test_channels_group(self):
        favs = [SHOW, CHANNEL, FILM]
        self.assertEqual([i for i, _ in fv.wanted(favs, 'video')], [0, 1, 2])
        self.assertEqual([i for i, _ in fv.wanted(favs, 'video', channels=False)], [0, 2])
        self.assertEqual([i for i, _ in fv.wanted(favs, 'channels')], [1])

    def test_builtin(self):
        self.assertEqual(fv.builtin(SHOW), 'ActivateWindow(videos,"videodb://tvshows/titles/412/",return)')
        self.assertEqual(fv.builtin(FILM), 'PlayMedia("nfs://nas/Movies/3 Godfathers (1948).mkv")')
        self.assertEqual(fv.builtin(ADDON), 'RunScript("script.skippy")')
        self.assertEqual(fv.builtin(SETTINGS), 'ActivateWindow(settings)')
        self.assertEqual(fv.builtin({'type': 'unknown'}), '')


if __name__ == '__main__':
    unittest.main()
