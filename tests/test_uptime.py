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


def test_from_seconds():
    from resources.lib.uptime import from_seconds
    assert from_seconds(30) == '0m'
    assert from_seconds(3725) == '1h 2m'
    assert from_seconds(1800000) == '20d 20h 0m'
    assert from_seconds(None) == ''


def test_system_seconds_is_a_number_or_none():
    from resources.lib.uptime import system_seconds
    value = system_seconds()
    assert value is None or value > 0


def test_health():
    from resources.lib.uptime import health
    assert health('58%', '2153MB', '3699MB', '46°C', '44°C') == ('good', '58', '2.1 / 3.6 GB')
    assert health('92%', '3400MB', '3699MB', '46°C', '44°C')[0] == 'memory'
    assert health('58%', '2153MB', '3699MB', '78°C', '44°C')[0] == 'warm'
    assert health('58%', '2153MB', '3699MB', '170°F', '')[0] == 'warm'
    assert health('', '', '', 'Not available', 'Not available') == ('good', '', '')
