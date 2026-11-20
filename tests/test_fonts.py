import os
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib import fonts

BASE = '''<?xml version="1.0" encoding="UTF-8"?>
<fonts>
	<fontset id="Default" idloc="31900">
		<font>
			<name>ui_24</name>
			<filename>Fig.ttf</filename>
			<size>24</size>
		</font>
		<font><name>display_48</name><filename>Fig.ttf</filename><size>48</size></font>
		<font><name>lyr1</name><filename>Boxing.ttf</filename><size>60</size></font>
	</fontset>

	<fontset id="Arial">
		<font><name>ui_24</name><filename>arial.ttf</filename><size>24</size></font>
		<font><name>display_48</name><filename>arial.ttf</filename><size>48</size></font>
		<font><name>lyr1</name><filename>Boxing.ttf</filename><size>60</size></font>
	</fontset>
</fonts>
'''


def named(text, fontset):
    root = ET.fromstring(text.encode('utf-8'))
    for node in root.findall('fontset'):
        if node.get('id') == fontset:
            return dict((f.findtext('name'), f.findtext('filename')) for f in node.findall('font'))
    return {}


class Fonts(unittest.TestCase):
    def test_follow_the_font_set(self):
        out = fonts.build(BASE, {})
        self.assertEqual(named(out, 'Default')['hm_ui_24'], 'Fig.ttf')
        self.assertEqual(named(out, 'Arial')['hm_ui_24'], 'arial.ttf')
        self.assertEqual(named(out, 'Arial')['hd_display_48'], 'arial.ttf')

    def test_section_choice(self):
        out = fonts.build(BASE, {'home': 'Arial', 'headings': 'Default'})
        self.assertEqual(named(out, 'Default')['hm_ui_24'], 'arial.ttf')
        self.assertEqual(named(out, 'Default')['lb_ui_24'], 'Fig.ttf')
        self.assertEqual(named(out, 'Arial')['hd_display_48'], 'Fig.ttf')
        self.assertEqual(named(out, 'Arial')['ui_24'], 'arial.ttf')

    def test_names_per_section(self):
        got = named(fonts.build(BASE, {}), 'Default')
        self.assertIn('st_ui_24', got)
        self.assertIn('pl_ui_24', got)
        self.assertNotIn('hd_ui_24', got)
        self.assertIn('hm_display_48', got)
        self.assertFalse([n for n in got if n.endswith('lyr1') and n != 'lyr1'])

    def test_idempotent(self):
        once = fonts.build(BASE, {'home': 'Arial'})
        self.assertEqual(fonts.build(once, {'home': 'Arial'}), once)
        self.assertEqual(fonts.build(once, {}), fonts.build(BASE, {}))
        self.assertEqual(fonts.strip(once).strip(), BASE.strip())

    def test_unknown_choice_follows(self):
        out = fonts.build(BASE, {'home': 'Nope', 'bogus': 'Arial'})
        self.assertEqual(named(out, 'Default')['hm_ui_24'], 'Fig.ttf')
        self.assertEqual(fonts.read_marker(out)['home'], '')

    def test_marker(self):
        self.assertIsNone(fonts.read_marker(BASE))
        out = fonts.build(BASE, {'player': 'Arial'})
        self.assertEqual(fonts.read_marker(out), {'home': '', 'library': '', 'headings': '', 'settings': '', 'player': 'Arial'})

    def test_one_file_family(self):
        out = fonts.build(BASE, {'library': 'Aeon Serif'})
        self.assertEqual(named(out, 'Arial')['lb_ui_24'], 'AeonSerif-Medium.ttf')
        self.assertEqual(named(out, 'Arial')['hm_ui_24'], 'arial.ttf')
        self.assertIn('<name>lb_ui_24</name><filename>AeonSerif-Medium.ttf</filename><size>24</size>', out)
        self.assertEqual(fonts.read_marker(out)['library'], 'Aeon Serif')

    def test_menu_labels_belong_to_home(self):
        self.assertEqual(fonts.section_name('aeon_title_66', 'home'), 'hm_aeon_title_66')
        self.assertEqual(fonts.section_name('aeon_title_66', ''), 'aeon_title_66')

    def test_preview_fonts(self):
        base = BASE.replace('<name>ui_24</name>', '<name>body_24</name>').replace('<name>ui_24</name>', '<name>body_24</name>')
        out = fonts.build(base, {})
        got = named(out, 'Default')
        self.assertEqual(fonts.families(base)[:2], ['Default', 'Arial'])
        self.assertEqual(got['pv0_b'], 'Fig.ttf')                       # follows the font set
        self.assertEqual(got['pv1_b'], 'Fig.ttf')                       # Default
        self.assertEqual(got['pv2_b'], 'arial.ttf')                     # Arial
        self.assertEqual(got['pv3_b'], 'Barlow-Regular.ttf')            # first four-weight family
        serif = fonts.families(base).index('Aeon Serif') + 1
        self.assertEqual(got['pv%d_b' % serif], 'AeonSerif-Medium.ttf')   # a one-file family
        self.assertEqual(named(out, 'Arial')['pv0_b'], 'arial.ttf')
        self.assertNotIn('pv0_t', got)                                  # the font set has no ui_28_bold
        self.assertEqual(fonts.build(out, {}), out)

    def test_has_bold(self):
        sets = {'Two': {'ui_24': '<filename>a.ttf</filename>', 'ui_24_bold': '<filename>a-bold.ttf</filename>'},
                'One': {'ui_24': '<filename>a.ttf</filename>', 'ui_24_bold': '<filename>a.ttf</filename>'},
                'None': {'ui_24': '<filename>a.ttf</filename>'}}
        self.assertTrue(fonts.has_bold('Two', sets))
        self.assertFalse(fonts.has_bold('One', sets))
        self.assertFalse(fonts.has_bold('None', sets))
        self.assertFalse(fonts.has_bold('Aeon Serif', sets))

    def test_weighted_family(self):
        base = BASE.replace('Fig.ttf</filename>\n\t\t\t<size>24', 'Figtree-Bold.ttf</filename>\n\t\t\t<size>24')
        base = base.replace('<filename>Fig.ttf</filename><size>48', '<filename>Figtree-Regular.ttf</filename><size>48')
        out = fonts.build(base, {'home': 'Barlow', 'headings': 'Barlow'})
        self.assertEqual(named(out, 'Default')['hm_ui_24'], 'Barlow-Bold.ttf')
        self.assertEqual(named(out, 'Arial')['hm_ui_24'], 'Barlow-Bold.ttf')
        self.assertEqual(named(out, 'Arial')['hd_display_48'], 'Barlow-Regular.ttf')
        self.assertEqual(named(out, 'Arial')['lb_ui_24'], 'arial.ttf')
        self.assertTrue(fonts.has_bold('Barlow', {}))
        self.assertIn('Barlow', fonts.families(base))
        self.assertEqual(fonts.weighted_files('Barlow')[3], 'Barlow-Bold.ttf')

    def test_headings_follow_their_section(self):
        out = fonts.build(BASE, {'home': 'Arial'})
        self.assertEqual(named(out, 'Default')['hm_display_48'], 'arial.ttf')      # Home menu labels follow Home
        self.assertEqual(named(out, 'Default')['lb_display_48'], 'Fig.ttf')
        self.assertEqual(named(out, 'Default')['hd_display_48'], 'Fig.ttf')

    def test_headings_choice_wins_everywhere(self):
        out = fonts.build(BASE, {'home': 'Arial', 'headings': 'Default'})
        self.assertEqual(named(out, 'Arial')['hm_display_48'], 'Fig.ttf')
        self.assertEqual(named(out, 'Arial')['lb_display_48'], 'Fig.ttf')
        self.assertEqual(named(out, 'Arial')['hd_display_48'], 'Fig.ttf')
        self.assertEqual(named(out, 'Default')['hm_ui_24'], 'arial.ttf')

    def test_files(self):
        self.assertEqual(fonts.files(BASE), {'Default': ['Fig.ttf'], 'Arial': ['arial.ttf']})

    def test_presets(self):
        self.assertEqual(fonts.preset_of({}), 'figtree')
        self.assertEqual(fonts.preset_of({'headings': 'Fraunces Bold'}), 'fraunces')
        both = fonts.preset_choices('Oswald SemiBold', 'Source Sans 3 (cut)')
        self.assertEqual(both['headings'], 'Oswald SemiBold')
        self.assertEqual(both['player'], 'Source Sans 3 (cut)')
        self.assertEqual(fonts.preset_of(both), 'oswald')
        self.assertEqual(fonts.preset_of({'home': 'Barlow'}), '')
        for _key, _name, heading, body in fonts.PRESETS:
            for family in (heading, body):
                self.assertTrue(not family or family in fonts.ONEFILE or family in fonts.PATTERN, family)

    def test_heading_face(self):
        out = fonts.build(BASE, fonts.preset_choices('Bebas Neue', ''))
        self.assertEqual(named(out, 'Default')['hd_display_48'], 'BebasNeue-Regular.ttf')
        self.assertEqual(named(out, 'Default')['lb_display_48'], 'BebasNeue-Regular.ttf')
        self.assertEqual(named(out, 'Default')['lb_ui_24'], 'Fig.ttf')
        self.assertEqual(fonts.read_marker(out)['headings'], 'Bebas Neue')
        # the heading faces come after every older family: older preview numbers stay
        names = fonts.families(BASE)
        self.assertLess(names.index('Noto Mono'), names.index('Fraunces Bold'))
        self.assertEqual(names[-1], 'TASA Explorer ExtraBold')

    def test_named_weights(self):
        self.assertEqual(fonts.weighted_files('LT Veritas')[2], 'LTVeritas-Medium.ttf')
        self.assertEqual(fonts.weighted_files('LT Superior')[3], 'LTSuperior-Bold.otf')
        base = BASE.replace('Fig.ttf</filename>\n\t\t\t<size>24', 'Figtree-Bold.ttf</filename>\n\t\t\t<size>24')
        out = fonts.build(base, {'library': 'Cooper Hewitt'})
        self.assertEqual(named(out, 'Default')['lb_ui_24'], 'CooperHewitt-Bold.otf')
        self.assertEqual(len(fonts.PRESETS), 19)
        self.assertEqual(len(set(p[0] for p in fonts.PRESETS)), 19)

    def test_section_name(self):
        self.assertEqual(fonts.section_name('ui_24', 'home'), 'hm_ui_24')
        self.assertEqual(fonts.section_name('display_48', 'home'), 'hm_display_48')
        self.assertEqual(fonts.section_name('display_48', ''), 'hd_display_48')
        self.assertEqual(fonts.section_name('ui_24', ''), 'ui_24')
        self.assertEqual(fonts.section_name('lyr1', 'player'), 'lyr1')
        self.assertEqual(fonts.section_name('$PARAM[font]', 'home'), '$PARAM[font]')

    def test_capitals_twins_follow_the_settings_face(self):
        out = fonts.build(BASE, {})
        ET.fromstring(out.encode('utf-8'))
        self.assertIn('<font><name>uc_st_ui_24</name><filename>Fig.ttf</filename><size>24</size>'
                      '<style>uppercase</style></font>', out)
        self.assertEqual(named(out, 'Arial')['uc_st_ui_24'], 'arial.ttf')
        self.assertEqual(named(fonts.build(BASE, {'settings': 'Arial'}), 'Default')['uc_st_ui_24'], 'arial.ttf')
        # rebuilt, not doubled
        self.assertEqual(fonts.build(out, {}).count('<name>uc_st_ui_24</name>'), 2)

    def test_uppercase_keeps_own_style(self):
        self.assertEqual(fonts.uppercase('<size>24</size><style>bold</style>'), '<size>24</size><style>bold uppercase</style>')
        self.assertEqual(fonts.uppercase('<size>24</size>'), '<size>24</size><style>uppercase</style>')


if __name__ == '__main__':
    unittest.main()
