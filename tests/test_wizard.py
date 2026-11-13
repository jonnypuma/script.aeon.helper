# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import wizard


class TestWizard(unittest.TestCase):
    def test_nothing_to_do(self):
        self.assertEqual(wizard.plan('aeon', False, 'SKINDEFAULT', 'SKINDEFAULT'), [])
        self.assertEqual(wizard.plan('aeon', False, 'Nord', 'Nord.xml'), [])
        self.assertEqual(wizard.plan('glass', True, 'Nord', 'SKINDEFAULT'), [])      # palettes do not count with Glass
        self.assertEqual(wizard.plan('', False, '', 'Nord'), [])

    def test_palette(self):
        self.assertEqual(wizard.plan('aeon', False, 'Nord', 'SKINDEFAULT'), [('palette', 'Nord')])
        self.assertEqual(wizard.plan('aeon', False, 'SKINDEFAULT', 'Dracula.xml'), [('palette', 'SKINDEFAULT')])
        self.assertEqual(wizard.plan('aeon', False, 'Nord', ''), [('palette', 'Nord')])

    def test_theme(self):
        self.assertEqual(wizard.plan('glass', False, 'Nord', 'Nord'), [('vglass', True), ('theme', 'Glass')])
        self.assertEqual(wizard.plan('aeon', True, 'SKINDEFAULT', 'SKINDEFAULT'), [('vglass', False), ('theme', 'Aeon')])
        # back to Aeon with a new palette: the palette is remembered before the theme changes
        self.assertEqual(wizard.plan('aeon', True, 'Nord', 'SKINDEFAULT'), [('vglass', False), ('palette', 'Nord'), ('theme', 'Aeon')])

    def test_palette_name(self):
        self.assertEqual(wizard.palette_name('Nord.xml'), 'Nord')
        self.assertEqual(wizard.palette_name('Rose-Pine'), 'Rose-Pine')
        self.assertEqual(wizard.palette_name(''), 'SKINDEFAULT')
        self.assertEqual(wizard.palette_name('SKINDEFAULT'), 'SKINDEFAULT')
        self.assertEqual(wizard.palette_name('defaults.xml'), 'SKINDEFAULT')

    def test_palette_index(self):
        names = ['Nord', 'Abyss', 'Dune']
        self.assertEqual(wizard.palette_index('SKINDEFAULT', names), 0)
        self.assertEqual(wizard.palette_index('Abyss', names), 1)
        self.assertEqual(wizard.palette_index('Nord', names), 3)
        self.assertEqual(wizard.palette_index('Gone', names), 0)

    def test_list_order_matches_skin(self):
        # the skin's list (wizgen.py) is SKINDEFAULT + the colors files sorted; the helper must count the same way
        skin = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'skin.aeon.fuse')
        colors = os.path.join(skin, 'colors')
        wizard_xml = os.path.join(skin, '1080i', 'Custom_1173_SetupWizard.xml')
        if not (os.path.isdir(colors) and os.path.isfile(wizard_xml)):
            self.skipTest('skin not beside the helper')
        # the Fused Glass theme's own colours are not a palette (palette.names leaves them out too)
        names = [os.path.splitext(n)[0] for n in os.listdir(colors) if n.endswith('.xml') and n not in ('defaults.xml', 'Fused Glass.xml')]
        import re
        text = open(wizard_xml, encoding='utf-8').read()
        listed = re.findall(r'SetProperty\(aeon\.wiz\.palette,([^,]+),home\)', text)
        self.assertEqual(listed, ['SKINDEFAULT'] + sorted(names))
        self.assertEqual(wizard.palette_index(listed[7], names), 7)

    def test_menu_switch(self):
        positions = ['movies', 'tv', 'music', 'off', 'favourites'] + ['off'] * 8
        hidden = [False, False, False, False, True] + [False] * 8
        self.assertEqual(wizard.menu_switch(positions, hidden, 'tv'), ('hide', 2))
        self.assertEqual(wizard.menu_switch(positions, hidden, 'favourites'), ('show', 5))
        self.assertEqual(wizard.menu_switch(positions, hidden, 'weather'), ('place', 4))
        full = ['movies'] * 13
        self.assertEqual(wizard.menu_switch(full, [False] * 13, 'weather'), ('full', 0))

    def test_can_restart(self):
        self.assertTrue(wizard.can_restart('linux'))
        self.assertFalse(wizard.can_restart('windows'))      # RestartApp only quits there
        self.assertFalse(wizard.can_restart('android'))


if __name__ == '__main__':
    unittest.main()
