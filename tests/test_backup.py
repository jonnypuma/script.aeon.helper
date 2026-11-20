# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import backup


SKIN = [{'id': 'aeon.fglass', 'type': 'boolean', 'value': True}, {'id': 'aeon.vglass', 'type': 'boolean', 'value': True},
        {'id': 'aeon.palette', 'type': 'string', 'value': 'Nord'}, {'id': 'aeon.fgmenu', 'type': 'string', 'value': ''},
        {'id': 'aeon.font', 'type': 'string', 'value': 'figtree'}, {'id': 'aeon.rt.setrow', 'type': 'string', 'value': 'videodb://x/'}]
KODI = {'lookandfeel.skintheme': 'Fused Glass', 'lookandfeel.skincolors': 'Fused Glass.xml', 'lookandfeel.font': 'Default',
        'lookandfeel.skinzoom': 0}


class TestBackup(unittest.TestCase):
    def data(self):
        return backup.build(SKIN, KODI, '0.56.42', '2026-11-18 14:05')

    def test_build_and_load(self):
        d = self.data()
        self.assertEqual(d['settings'], {'aeon.fglass': True, 'aeon.vglass': True, 'aeon.palette': 'Nord', 'aeon.fgmenu': '',
                                         'aeon.font': 'figtree'})
        self.assertNotIn('lookandfeel.skinzoom', d['kodi'])
        self.assertEqual(backup.load(backup.dump(d)), d)
        self.assertIsNone(backup.load('not json'))
        self.assertIsNone(backup.load('{"format": "other", "version": 1, "settings": {}}'))
        self.assertIsNone(backup.load('{"format": "aeon-fuse-settings", "version": 9, "settings": {}}'))
        self.assertIsNone(backup.load('[]'))

    def test_plan(self):
        d = self.data()
        now = dict(d['settings'])
        self.assertEqual(backup.plan(d, now), [])
        now.update({'aeon.fglass': False, 'aeon.palette': 'Ocean', 'aeon.zzz': 'kept'})
        self.assertEqual(backup.plan(d, now), [('aeon.fglass', True), ('aeon.palette', 'Nord')])
        # a setting this Kodi does not know yet is set; a type clash is left alone
        d['settings']['aeon.new'] = 'x'
        d['settings']['aeon.font'] = True
        self.assertEqual(backup.plan(d, now), [('aeon.fglass', True), ('aeon.new', 'x'), ('aeon.palette', 'Nord')])
        # unknown and off / empty are the same as missing
        d2 = {'settings': {'aeon.off': False, 'aeon.empty': '', 'aeon.rt.setrow': 'videodb://y/'}}
        self.assertEqual(backup.plan(d2, {}), [])

    def test_switches_first(self):
        d = {'settings': {'aeon.a': 'x', 'aeon.vglass': False, 'aeon.fglass': True}}
        self.assertEqual([k for k, _ in backup.plan(d, {'aeon.vglass': True})], ['aeon.fglass', 'aeon.vglass', 'aeon.a'])

    def test_kodi_plan(self):
        d = self.data()
        self.assertEqual(backup.kodi_plan(d, KODI), [])
        now = dict(KODI, **{'lookandfeel.skintheme': 'Aeon', 'lookandfeel.skincolors': 'Nord.xml'})
        self.assertEqual(backup.kodi_plan(d, now), [('lookandfeel.skincolors', 'Fused Glass.xml'),
                                                    ('lookandfeel.skintheme', 'Fused Glass')])

    def test_fonts_and_builtin(self):
        self.assertTrue(backup.fonts_changed([('aeon.fontkey', 'x')]))
        self.assertFalse(backup.fonts_changed([('aeon.palette', 'x')]))
        self.assertEqual(backup.builtin('aeon.a', True), 'Skin.SetBool(aeon.a)')
        self.assertEqual(backup.builtin('aeon.a', False), 'Skin.Reset(aeon.a)')
        self.assertEqual(backup.builtin('aeon.a', ''), 'Skin.Reset(aeon.a)')
        self.assertEqual(backup.builtin('aeon.a', 'a, "b" \\c'), 'Skin.SetString(aeon.a,"a, \\"b\\" \\\\c")')
        self.assertEqual(backup.file_name('2026-11-18 14:05'), 'aeon-fuse-settings-20261118-1405.json')


if __name__ == '__main__':
    unittest.main()
