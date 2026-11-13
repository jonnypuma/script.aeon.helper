import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib.channels import describe, last_played, progress

CHANNELS = [{'channelid': 1, 'label': 'One', 'lastplayed': '2026-11-08'}, {'channelid': 2, 'label': 'Two', 'lastplayed': ''},
            {'channelid': 3, 'label': 'Three', 'lastplayed': '1970-01-01 00:00:00'}, {'channelid': 4, 'label': 'Four', 'lastplayed': '2026-11-09 20:00:00'}]


class Channels(unittest.TestCase):
    def test_last_played_order_and_never_played(self):
        self.assertEqual([c['channelid'] for c in last_played(CHANNELS)], [4, 1])
        self.assertEqual([c['channelid'] for c in last_played(CHANNELS, limit=1)], [4])
        self.assertEqual(last_played([]), [])

    def test_progress(self):
        self.assertEqual(progress({'progresspercentage': 41.6}), '42')
        self.assertEqual(progress({}), '')
        self.assertEqual(progress(None), '')

    def test_describe(self):
        got = describe({'channelid': 7, 'label': 'News', 'icon': 'i.png', 'channelnumber': 12,
                        'broadcastnow': {'title': 'Now', 'plot': 'p', 'progresspercentage': 10}, 'broadcastnext': {'title': 'Next'}})
        self.assertEqual((got['label'], got['now'], got['next'], got['progress'], got['icon'], got['channelid'], got['number']),
                         ('News', 'Now', 'Next', '10', 'i.png', 7, '12'))
        self.assertEqual(describe({'label': 'Bare'})['now'], '')


if __name__ == '__main__':
    unittest.main()
