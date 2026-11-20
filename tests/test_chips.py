# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib import chips


class Chips(unittest.TestCase):
    def test_defaults(self):
        on = chips.shown(lambda flag: False)
        self.assertEqual([chips.CHIPS[i][0] for i in on], ['res', 'aspect', 'hdr', 'dvp', 'audio', 'channels', 'source'])
        self.assertEqual(chips.summary(on), '7 / 17')

    def test_switches(self):
        flags = {'aeon.hide.hdr', 'aeon.chip.subs'}
        on = chips.shown(lambda flag: flag in flags)
        keys = [chips.CHIPS[i][0] for i in on]
        self.assertNotIn('hdr', keys)
        self.assertIn('subs', keys)

    def test_builtins_round_trip(self):
        keys = [k for k, _s, _f, _h in chips.CHIPS]
        sel = [keys.index('res'), keys.index('audio'), keys.index('subs')]
        calls = chips.builtins(sel)
        state = set()
        for c in calls:
            name = c[c.index('(') + 1:-1]
            if c.startswith('Skin.SetBool'):
                state.add(name)
        self.assertEqual(chips.shown(lambda flag: flag in state), sel)
        self.assertIn('Skin.SetBool(aeon.hide.hdr)', calls)
        self.assertIn('Skin.Reset(aeon.hide.res)', calls)
        self.assertIn('Skin.SetBool(aeon.chip.subs)', calls)
        self.assertIn('Skin.Reset(aeon.chip.size)', calls)
        self.assertIn('Skin.Reset(aeon.chip.3d)', calls)

    def test_sidecar_parts(self):
        keys = [k for k, _s, _f, _h in chips.CHIPS]
        self.assertEqual(keys[keys.index('source'):keys.index('source') + 4], ['source', 'vsource', 'vcodec', 'edition'])
        flags = [f for _k, _s, f, _h in chips.CHIPS]
        self.assertEqual(len(set(flags)), len(flags))
        self.assertEqual(len(set(s for _k, s, _f, _h in chips.CHIPS)), len(chips.CHIPS))


if __name__ == '__main__':
    unittest.main()
