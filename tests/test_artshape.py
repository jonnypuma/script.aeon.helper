import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib.artshape import best, candidates, fits, is_local, split, type_from_name, unwrap

SHOW = 'nfs://192.168.0.9/Media/TV/Cheers/'


class ArtShape(unittest.TestCase):
    def test_shapes(self):
        self.assertTrue(fits('poster', 1080, 1620))           # 2:3
        self.assertTrue(fits('poster', 1000, 1426))           # DVD cover
        self.assertFalse(fits('poster', 500, 281))            # the Cheers landscape "poster"
        self.assertFalse(fits('poster', 1000, 1000))          # square
        self.assertTrue(fits('banner', 758, 140))
        self.assertFalse(fits('banner', 1000, 1500))
        self.assertTrue(fits('landscape', 1920, 1080))
        self.assertFalse(fits('fanart', 1080, 1620))
        self.assertTrue(fits('clearlogo', 800, 310))          # no rule: always fits
        self.assertTrue(fits('poster', 0, 0))                 # unknown size: left alone

    def test_unwrap_and_local(self):
        self.assertEqual(unwrap('image://nfs%3a%2f%2f192.168.0.9%2fMedia%2fTV%2fCheers%2fseason06-poster.png/'),
                         SHOW + 'season06-poster.png')
        self.assertEqual(unwrap(SHOW + 'poster.jpg'), SHOW + 'poster.jpg')
        self.assertTrue(is_local(SHOW + 'season06-poster.png'))
        self.assertTrue(is_local('C:\\Films\\Heat (1995)\\poster.JPG'))
        self.assertFalse(is_local('https://image.tmdb.org/t/p/original/abc.jpg'))
        self.assertFalse(is_local('video@' + SHOW + 'S01E01.mkv'))
        self.assertEqual(split('C:\\Films\\Heat\\poster.jpg'), ('C:\\Films\\Heat\\', 'poster.jpg'))

    def test_candidates_same_name_other_extension(self):
        names = ['season06-poster.png', 'season06-poster.jpg', 'season06-thumb.png', 'season07-poster.jpg', 'poster.jpg']
        self.assertEqual(candidates(SHOW + 'season06-poster.png', 'poster', names), [SHOW + 'season06-poster.jpg'])
        self.assertEqual(candidates(SHOW + 'season06-poster.jpg', 'poster', names), [SHOW + 'season06-poster.png'])

    def test_candidates_show_poster_also_folder(self):
        names = ['poster.png', 'poster.jpg', 'folder.jpg', 'fanart.jpg']
        self.assertEqual(candidates(SHOW + 'poster.png', 'poster', names), [SHOW + 'poster.jpg', SHOW + 'folder.jpg'])
        # a film's own poster name never borrows folder.jpg
        film = 'nfs://h/Films/Heat/Heat.1995-poster.png'
        self.assertEqual(candidates(film, 'poster', ['Heat.1995-poster.png', 'Heat.1995-poster.jpg', 'folder.jpg']),
                         ['nfs://h/Films/Heat/Heat.1995-poster.jpg'])

    def test_type_from_name(self):
        self.assertEqual(type_from_name('season06-poster.png'), 'poster')
        self.assertEqual(type_from_name('folder.jpg'), 'poster')
        self.assertEqual(type_from_name('Heat.1995-banner.jpg'), 'banner')
        self.assertEqual(type_from_name('landscape.jpg'), 'landscape')
        self.assertEqual(type_from_name('fanart12.jpg'), 'fanart')
        self.assertEqual(type_from_name('season01-fanart.png'), 'fanart')
        self.assertEqual(type_from_name('season06-thumb.png'), '')
        self.assertEqual(type_from_name('clearlogo.png'), '')
        self.assertEqual(type_from_name('postermaker.jpg'), '')

    def test_best(self):
        self.assertEqual(best('poster', [('a', 500, 281), ('b', 1080, 1620), ('c', 680, 1000)]), 'b')
        self.assertIsNone(best('poster', [('a', 500, 281), ('b', 1920, 1080)]))


if __name__ == '__main__':
    unittest.main()
