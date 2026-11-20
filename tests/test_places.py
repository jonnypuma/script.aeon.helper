import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import places  # noqa: E402


class PlacesTest(unittest.TestCase):
    def test_default_all_on(self):
        self.assertEqual(places.shown('rate', lambda f: False), list(range(len(places.places('rate')))))
        self.assertNotIn('ss', [p for p, _s in places.places('rate')])
        self.assertNotIn('pvr', [p for p, _s in places.places('chip')])

    def test_off_flag(self):
        off = {'aeon.rateoff.spot', 'aeon.chipoff.lib'}
        now = places.shown('rate', lambda f: f in off)
        self.assertNotIn([p for p, _s in places.places('rate')].index('spot'), now)
        self.assertEqual(len(now), len(places.places('rate')) - 1)

    def test_builtins_roundtrip(self):
        calls = places.builtins('chip', [0, 2])
        self.assertEqual(calls[0], 'Skin.Reset(aeon.chipoff.lib)')
        self.assertEqual(calls[1], 'Skin.SetBool(aeon.chipoff.info)')
        set_on = {c[len('Skin.SetBool('):-1] for c in calls if c.startswith('Skin.SetBool')}
        self.assertEqual(places.shown('chip', lambda f: f in set_on), [0, 2])

    def test_summary(self):
        self.assertEqual(places.summary('chip', [0, 1, 1]), '2 / 6')


if __name__ == '__main__':
    unittest.main()
