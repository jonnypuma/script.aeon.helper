# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import ctxmenu


class TestCtxMenu(unittest.TestCase):
    def test_refresh_call(self):
        self.assertEqual(ctxmenu.refresh_call('movie', '56'), ('VideoLibrary.RefreshMovie', {'movieid': 56, 'ignorenfo': False}))
        self.assertEqual(ctxmenu.refresh_call('Episode', 7)[0], 'VideoLibrary.RefreshEpisode')
        self.assertEqual(ctxmenu.refresh_call('tvshow', '3')[1], {'tvshowid': 3, 'ignorenfo': False})
        self.assertIsNone(ctxmenu.refresh_call('season', '3'))
        self.assertIsNone(ctxmenu.refresh_call('movie', ''))
        self.assertIsNone(ctxmenu.refresh_call('movie', '-1'))
        self.assertIsNone(ctxmenu.refresh_call('album', '9'))

    def test_refresh_toast(self):
        self.assertEqual(ctxmenu.refresh_progress(0, 0), 10)
        self.assertEqual(ctxmenu.refresh_progress(3, 24), 12)
        self.assertEqual(ctxmenu.refresh_progress(0, 24), 1)
        self.assertEqual(ctxmenu.refresh_progress(30, 24), 100)
        self.assertEqual(ctxmenu.refresh_line(3, 24, 1, 3, 'Pilot'), 'Episode 3 of 24: S01E03 Pilot')
        self.assertEqual(ctxmenu.refresh_line(3, 24), 'Episode 3 of 24')
        self.assertEqual(ctxmenu.refresh_line(0, 0, title='Reading the information'), 'Reading the information')
        self.assertEqual(ctxmenu.refresh_line(2, 5, 0, 0, 'Special'), 'Episode 2 of 5: Special')

    def test_refresh_finished(self):
        self.assertFalse(ctxmenu.refresh_finished('movie', [], 0, 0, 5))
        self.assertTrue(ctxmenu.refresh_finished('movie', ['movie'], 0, 0, 5))
        self.assertFalse(ctxmenu.refresh_finished('tvshow', ['tvshow', 'episode'], 3, 1, 5))
        self.assertTrue(ctxmenu.refresh_finished('tvshow', ['tvshow', 'episode', 'episode', 'episode'], 3, 0, 9))
        self.assertTrue(ctxmenu.refresh_finished('tvshow', ['tvshow', 'episode'], 3, 21, 30))      # quiet for 20 s
        self.assertFalse(ctxmenu.refresh_finished('tvshow', [], 3, 0, 100))
        self.assertTrue(ctxmenu.refresh_finished('tvshow', [], 3, 0, 151))                       # hard stop

    def test_library_for(self):
        self.assertEqual(ctxmenu.library_for('album', False, True), 'music')
        self.assertEqual(ctxmenu.library_for('episode', True, False), 'video')
        self.assertEqual(ctxmenu.library_for('', True, False), 'music')
        self.assertEqual(ctxmenu.library_for('', False, True), 'video')
        self.assertEqual(ctxmenu.library_for('', False, False), '')

    def test_order_and_moves(self):
        self.assertEqual(ctxmenu.read_order(['', '', '', '']), ['refresh', 'update', 'clean', 'shot'])
        self.assertEqual(ctxmenu.read_order(['shot', 'clean', 'update', 'refresh']), ['shot', 'clean', 'update', 'refresh'])
        self.assertEqual(ctxmenu.read_order(['shot', 'shot', 'update', 'refresh']), list(ctxmenu.ACTIONS))
        order = list(ctxmenu.ACTIONS)
        self.assertEqual(ctxmenu.moved(order, 4, -1), (['refresh', 'update', 'shot', 'clean'], 3))
        self.assertEqual(ctxmenu.moved(order, 1, 1), (['update', 'refresh', 'clean', 'shot'], 2))
        self.assertEqual(ctxmenu.moved(order, 1, -1), (order, 1))
        self.assertEqual(ctxmenu.moved(order, 4, 1), (order, 4))

    def test_addon_xml_has_every_item_at_every_place(self):
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'addon.xml')
        with open(here, encoding='utf-8') as handle:
            xml = handle.read()
        self.assertIn(ctxmenu.addon_items(), xml)
        self.assertEqual(xml.count('<item library="context.py"'), 16)
        # the default order without any skin string set: place 1 = refresh, place 4 = screenshot (on by default)
        self.assertIn('String.IsEmpty(Skin.String(aeon.ctx.pos1))', ctxmenu.at_place(4, 'shot'))
        self.assertNotIn('IsEmpty', ctxmenu.at_place(1, 'shot'))
        self.assertEqual(ctxmenu.is_on('shot'), '!Skin.HasSetting(aeon.ctx.noshot)')


if __name__ == '__main__':
    unittest.main()
