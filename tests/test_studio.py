# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import studio


class TestStudio(unittest.TestCase):
    def test_first(self):
        self.assertEqual(studio.first('Carnival Films / BBC Film / Heyday Films / NBCUniversal'), 'Carnival Films')
        self.assertEqual(studio.first('Hulu'), 'Hulu')
        self.assertEqual(studio.first('TNT (US)'), 'TNT (US)')
        self.assertEqual(studio.first('AC/DC Films / B'), 'AC/DC Films')      # a slash inside a name stays
        self.assertEqual(studio.first(' / B'), 'B')
        self.assertEqual(studio.first(''), '')
        self.assertEqual(studio.first(None), '')


if __name__ == '__main__':
    unittest.main()
