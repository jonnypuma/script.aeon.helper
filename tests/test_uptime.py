import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib.uptime import short


class Uptime(unittest.TestCase):
    def test_days(self):
        self.assertEqual(short('8 Days, 15 Hours, 2 Minutes'), '8d 15h 2m')

    def test_hours(self):
        self.assertEqual(short('3 Hours, 4 Minutes'), '3h 4m')

    def test_minutes(self):
        self.assertEqual(short('4 Minutes'), '4m')

    def test_other_language(self):
        self.assertEqual(short('8 dager, 15 timer, 02 minutter'), '8d 15h 2m')

    def test_unknown_shape(self):
        self.assertEqual(short(''), '')
        self.assertEqual(short(None), '')
        self.assertEqual(short('Busy'), '')
        self.assertEqual(short('1 2 3 4'), '1 2 3 4')


if __name__ == '__main__':
    unittest.main()
