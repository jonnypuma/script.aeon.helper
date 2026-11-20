# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import palscope, wizard


class TestPalScope(unittest.TestCase):
    def test_split(self):
        self.assertEqual(palscope.split('Nord'), ('Nord', ''))
        self.assertEqual(palscope.split('Nord.xml'), ('Nord', ''))
        self.assertEqual(palscope.split('Nord (menus).xml'), ('Nord', 'menus'))
        self.assertEqual(palscope.split('Rose-Pine-Moon (library)'), ('Rose-Pine-Moon', 'library'))
        self.assertEqual(palscope.split(''), ('SKINDEFAULT', ''))
        self.assertEqual(palscope.split('defaults.xml'), ('SKINDEFAULT', ''))
        self.assertEqual(palscope.split('SKINDEFAULT'), ('SKINDEFAULT', ''))

    def test_file_for(self):
        self.assertEqual(palscope.file_for('Nord', ''), 'Nord')
        self.assertEqual(palscope.file_for('Nord', 'menus'), 'Nord (menus)')
        self.assertEqual(palscope.file_for('Nord', 'library'), 'Nord (library)')
        self.assertEqual(palscope.file_for('SKINDEFAULT', 'menus'), 'SKINDEFAULT')
        self.assertEqual(palscope.file_for('', 'library'), 'SKINDEFAULT')

    def test_round_trip(self):
        for scope in palscope.SCOPES:
            self.assertEqual(palscope.split(palscope.file_for('Space-Gray', scope)), ('Space-Gray', scope))

    def test_variants_left_out(self):
        self.assertTrue(palscope.is_variant('Nord (menus)'))
        self.assertFalse(palscope.is_variant('Nord'))
        self.assertFalse(palscope.is_variant('Fused Glass'))

    def test_wizard_name_drops_scope(self):
        self.assertEqual(wizard.palette_name('Nord (library).xml'), 'Nord')
        self.assertEqual(wizard.palette_name('Nord (menus)'), 'Nord')


if __name__ == '__main__':
    unittest.main()
