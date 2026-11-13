# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import boxart


class TestBoxArt(unittest.TestCase):
    def test_episode_uses_its_thumb(self):
        self.assertEqual(boxart.art_keys('episode')[0], 'thumb')
        self.assertEqual(boxart.art_keys(' Episode ')[0], 'thumb')

    def test_others_use_the_poster(self):
        for dbtype in ('movie', 'tvshow', 'season', 'set', '', None):
            self.assertEqual(boxart.art_keys(dbtype)[0], 'poster')
        self.assertIn('album.thumb', boxart.art_keys('album'))


    def test_spot_list(self):
        self.assertEqual(boxart.spot_list('movies'), 9421)
        self.assertEqual(boxart.spot_list('custom2'), 9412)
        self.assertEqual(boxart.spot_list('planner'), 9414)
        self.assertEqual(boxart.spot_list('pictures'), 0)
        self.assertEqual(boxart.spot_list(''), 0)


    def test_is_widget_list(self):
        self.assertTrue(boxart.is_widget_list('9401'))
        self.assertTrue(boxart.is_widget_list(9406))
        self.assertFalse(boxart.is_widget_list('9421'))
        self.assertFalse(boxart.is_widget_list(''))


if __name__ == '__main__':
    unittest.main()
