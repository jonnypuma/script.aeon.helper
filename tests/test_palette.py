# -*- coding: utf-8 -*-
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
for name in ('xbmc', 'xbmcaddon', 'xbmcgui', 'xbmcvfs'):
    sys.modules.setdefault(name, types.ModuleType(name))
import palette


class TestPalette(unittest.TestCase):
    def test_effective_backdrop(self):
        # from the View settings strip the view's own backdrop wins
        self.assertEqual(palette.effective_backdrop('fanart', 'neutral', True), ('neutral', 'view'))
        self.assertEqual(palette.effective_backdrop('neutral', 'color', True), ('color', 'view'))
        # a view without its own choice follows the global one
        self.assertEqual(palette.effective_backdrop('fanart', '', True), ('fanart', 'global'))
        # from Skin settings only the global one counts
        self.assertEqual(palette.effective_backdrop('fanart', 'neutral', False), ('fanart', 'global'))
        self.assertEqual(palette.effective_backdrop('', '', False), ('', 'global'))


if __name__ == '__main__':
    unittest.main()
