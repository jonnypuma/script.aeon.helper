# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib import skinstyle


class SkinStyle(unittest.TestCase):
    def test_map(self):
        self.assertEqual(skinstyle.library_glass(''), '')
        self.assertEqual(skinstyle.library_glass('dark'), '')
        self.assertEqual(skinstyle.library_glass('glass'), 'clear')
        self.assertEqual(skinstyle.library_glass('frost'), 'frost')

    def test_builtin(self):
        self.assertIsNone(skinstyle.builtin('glass', 'clear'))
        self.assertIsNone(skinstyle.builtin('', ''))
        self.assertEqual(skinstyle.builtin('', 'clear'), 'Skin.Reset(aeon.fgmat)')
        self.assertEqual(skinstyle.builtin('', 'raised'), 'Skin.Reset(aeon.fgmat)')
        self.assertEqual(skinstyle.builtin('frost', 'raised'), 'Skin.SetString(aeon.fgmat,frost)')
        self.assertEqual(skinstyle.builtin('glass', ''), 'Skin.SetString(aeon.fgmat,clear)')

    def test_next(self):
        self.assertEqual(skinstyle.next_style(''), 'glass')
        self.assertEqual(skinstyle.next_style('glass'), 'frost')
        self.assertEqual(skinstyle.next_style('frost'), 'system')
        self.assertEqual(skinstyle.next_style('system'), '')
        self.assertEqual(skinstyle.next_style('dark'), 'glass')
        self.assertEqual(skinstyle.next_style('nonsense'), '')
        self.assertEqual(skinstyle.library_glass('system'), '')
        self.assertTrue(skinstyle.needs_restart('frost', 'system'))
        self.assertTrue(skinstyle.needs_restart('system', ''))
        self.assertFalse(skinstyle.needs_restart('', 'glass'))


if __name__ == '__main__':
    unittest.main()
