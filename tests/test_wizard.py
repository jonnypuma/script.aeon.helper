# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import wizard


class TestWizard(unittest.TestCase):
    NOW = {'theme': 'fused', 'menutheme': '', 'fgmenu': 'system', 'palette': 'Fused Glass.xml'}

    def test_nothing_to_do(self):
        self.assertEqual(wizard.plan(dict(self.NOW), self.NOW), [])
        aeon = {'theme': 'aeon', 'menutheme': 'mosaic', 'fgmenu': '', 'palette': 'Nord.xml'}
        self.assertEqual(wizard.plan({'theme': 'aeon', 'menutheme': 'mosaic', 'palette': 'Nord'}, aeon), [])
        # Bridge is the empty string; Aeon Glass counts Fuse only
        self.assertEqual(wizard.plan({'theme': 'aeon', 'menutheme': 'bridge', 'palette': 'Nord'}, dict(aeon, menutheme='')), [])
        glass = {'theme': 'glass', 'menutheme': 'mosaic', 'fgmenu': '', 'palette': ''}
        self.assertEqual(wizard.plan({'theme': 'glass', 'menutheme': '', 'palette': 'Nord'}, glass), [])

    def test_style(self):
        self.assertEqual(wizard.plan(dict(self.NOW, fgmenu='frost'), self.NOW), [('fgmenu', 'frost')])
        self.assertEqual(wizard.plan(dict(self.NOW, fgmenu=''), self.NOW), [('fgmenu', '')])
        aeon = {'theme': 'aeon', 'menutheme': '', 'fgmenu': '', 'palette': ''}
        # 0.3.126: Fuse is removed: picking it is the standard menus (the service moves anyone still on it at start)
        self.assertEqual(wizard.plan(dict(aeon, menutheme='fused'), aeon), [])
        self.assertEqual(wizard.plan(dict(aeon, menutheme='mosaic'), aeon), [('menutheme', 'mosaic')])
        glass = {'theme': 'glass', 'menutheme': '', 'fgmenu': '', 'palette': ''}
        self.assertEqual(wizard.plan(dict(glass, menutheme='fused'), glass), [])
        self.assertEqual(wizard.plan(dict(glass, menutheme='mosaic'), glass), [])

    def test_palette(self):
        aeon = {'theme': 'aeon', 'menutheme': '', 'fgmenu': '', 'palette': 'SKINDEFAULT'}
        self.assertEqual(wizard.plan(dict(aeon, palette='Nord'), aeon), [('palette', 'Nord')])
        self.assertEqual(wizard.plan(dict(aeon, palette='SKINDEFAULT'), dict(aeon, palette='Dracula.xml')), [('palette', 'SKINDEFAULT')])
        self.assertEqual(wizard.plan(dict(aeon, palette='Nord'), dict(aeon, palette='Nord (library).xml')), [])
        # palettes do not count in the glass themes
        self.assertEqual(wizard.plan(dict(self.NOW, palette='Nord'), self.NOW), [])

    def test_theme(self):
        self.assertEqual(wizard.plan(dict(self.NOW, theme='glass'), self.NOW), [('theme', 'glass')])
        # to Aeon with a new palette and a menu style: style and palette are set before the theme changes
        want = {'theme': 'aeon', 'menutheme': 'ledger', 'fgmenu': 'system', 'palette': 'Nord'}
        self.assertEqual(wizard.plan(want, self.NOW), [('menutheme', 'ledger'), ('palette', 'Nord'), ('theme', 'aeon')])
        self.assertEqual(wizard.KODI_THEME['fused'], 'Fused Glass')

    def test_theme_key(self):
        self.assertEqual(wizard.theme_key('Fused Glass'), 'fused')
        self.assertEqual(wizard.theme_key('Glass'), 'glass')
        self.assertEqual(wizard.theme_key('SKINDEFAULT'), 'aeon')
        self.assertEqual(wizard.theme_key(''), 'aeon')

    def test_defaults(self):
        calls, later = wizard.defaults('fused')
        self.assertEqual(later, {'fgmenu': 'system'})
        self.assertIn('Skin.Reset(aeon.fgshadow)', calls)
        self.assertIn('Skin.Reset(aeon.lowmenu)', calls)
        calls, later = wizard.defaults('aeon')
        self.assertEqual(later, {'menutheme': '', 'palette': 'SKINDEFAULT'})
        self.assertEqual(wizard.defaults('glass')[1], {'menutheme': ''})
        # every theme sets the same settings, so a change of theme never leaves one of them behind
        self.assertEqual(sorted(wizard.defaults('aeon')[0]), sorted(wizard.defaults('glass')[0]))

    def test_defaults_cover_the_wizard_rows(self):
        # each skin setting a wizard row changes is in the defaults table (skin.aeon.fuse beside the helper)
        import re
        skin = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'skin.aeon.fuse', '1080i', 'Custom_1173_SetupWizard.xml')
        if not os.path.isfile(skin):
            self.skipTest('skin not beside the helper')
        text = open(skin, encoding='utf-8').read()
        used = set(re.findall(r'Skin\.(?:SetString|Reset|ToggleSetting|SetBool)\((aeon\.[\w.]+)', text))
        used -= {'aeon.wizard.done'}
        used = set(u for u in used if not u.startswith('aeon.wiz.add.'))   # add-on ticks (addonrec batch), not settings
        missing = sorted(used - set(wizard.COMMON))
        self.assertEqual(missing, [])

    def test_aeon_library_defaults(self):
        # the user's defaults (2026-11-19): Color backdrop + Colors corner boxes for Aeon and Aeon Glass only
        for theme in ('aeon', 'glass'):
            self.assertEqual(wizard.DEFAULTS[theme]['aeon.vbg'], 'color')
            self.assertEqual(wizard.DEFAULTS[theme]['aeon.boxbg'], '')
        self.assertEqual(wizard.DEFAULTS['fused']['aeon.vbg'], '')

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

    def test_palette_pictures(self):
        # the wizard's palette list shows colors/<name>.xml with media/aeon/wizard/pal_<name>.png
        skin = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'skin.aeon.fuse')
        colors = os.path.join(skin, 'colors')
        if not os.path.isdir(colors):
            self.skipTest('skin not beside the helper')
        names = [os.path.splitext(n)[0] for n in os.listdir(colors) if n.endswith('.xml') and n not in ('defaults.xml', 'Fused Glass.xml')]
        names = [n for n in names if not (n.endswith(' (menus)') or n.endswith(' (library)'))]
        missing = [n for n in ['defaults'] + names if not os.path.isfile(os.path.join(skin, 'media', 'aeon', 'wizard', 'pal_%s.png' % n))]
        self.assertEqual(missing, [])

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
