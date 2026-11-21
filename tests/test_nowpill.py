import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for name in ('xbmc', 'xbmcgui'):
    sys.modules.setdefault(name, types.ModuleType(name))
from resources.lib.livetv import now_pill


class NowPill(unittest.TestCase):
    def test_half_and_minutes(self):
        self.assertEqual(now_pill('16:42'), {'aeon.gd.half': '16:30', 'aeon.gd.min': '12', 'aeon.gd.hidelbl': ''})
        self.assertEqual(now_pill('4:42 PM')['aeon.gd.half'], '4:30 PM')

    def test_hidden_ruler_label(self):
        self.assertEqual(now_pill('16:05')['aeon.gd.hidelbl'], '16:00')
        self.assertEqual(now_pill('16:25')['aeon.gd.hidelbl'], '16:30')
        self.assertEqual(now_pill('23:58')['aeon.gd.hidelbl'], '00:00')
        self.assertEqual(now_pill('12:52 PM')['aeon.gd.hidelbl'], '1:00 PM')
        self.assertEqual(now_pill('09:52 AM')['aeon.gd.hidelbl'], '10:00 AM')
        self.assertEqual(now_pill('11:55 AM')['aeon.gd.hidelbl'], '')

    def test_no_clock(self):
        self.assertEqual(now_pill(''), {'aeon.gd.half': '', 'aeon.gd.min': '', 'aeon.gd.hidelbl': ''})


if __name__ == '__main__':
    unittest.main()
