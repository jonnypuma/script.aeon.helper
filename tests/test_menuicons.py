import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib.menuicons import choices, default_icon, preselect, pretty

SKIN = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'skin.aeon.fuse', 'media')


class MenuIcons(unittest.TestCase):
    def test_default_icons(self):
        self.assertEqual(default_icon('movies'), 'aeon/icons/film.png')
        self.assertEqual(default_icon('sets'), 'aeon/icons/stack.png')
        self.assertEqual(default_icon('favourites'), 'aeon/icons/star.png')
        self.assertEqual(default_icon('custom2', 'library://video/movies/sets.xml/'), 'aeon/icons/stack.png')
        self.assertEqual(default_icon('custom1', 'plugin://plugin.video.youtube/'), 'aeon/icons/star.png')
        self.assertEqual(default_icon('custom3'), 'aeon/icons/star.png')

    def test_pretty(self):
        self.assertEqual(pretty('apple_tv-plus.png'), 'Apple tv plus')
        self.assertEqual(pretty('Crunchyroll.png'), 'Crunchyroll')
        self.assertEqual(pretty('icons/af3/3dtv.png'), '3dtv')

    def test_choices_order_and_filter(self):
        out = choices(['star.png', 'Play.png', 'play.png', 'film.png', 'notes.txt'], ['b.png', '_none.png', 'A.png'])
        self.assertEqual([p for _l, p in out], ['aeon/icons/film.png', 'aeon/icons/Play.png', 'aeon/icons/star.png',
                                               'icons/af3/A.png', 'icons/af3/b.png'])

    def test_preselect(self):
        entries = [('Default', ''), ('Film', 'aeon/icons/film.png'), ('A', 'icons/af3/A.png')]
        self.assertEqual(preselect(entries, 'icons/af3/A.png'), 2)
        self.assertEqual(preselect(entries, ''), 0)
        self.assertEqual(preselect(entries, 'icons/af3/gone.png'), 0)

    @unittest.skipUnless(os.path.isdir(SKIN), 'skin not next to the helper')
    def test_skin_has_the_icons(self):
        for key in ('movies', 'tv', 'music', 'search', 'system', 'livetv', 'power', 'sets', 'pictures', 'weather',
                    'planner', 'custom1'):
            self.assertTrue(os.path.isfile(os.path.join(SKIN, default_icon(key))), key)
        af3 = os.listdir(os.path.join(SKIN, 'icons', 'af3'))
        self.assertGreater(len(choices(os.listdir(os.path.join(SKIN, 'aeon', 'icons')), af3)), 1500)


if __name__ == '__main__':
    unittest.main()
