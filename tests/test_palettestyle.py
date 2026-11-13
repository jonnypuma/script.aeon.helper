import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib.palettestyle import contrast, parse, readable, style

DEFAULTS = parse('<color name="aeon_white">ffe9e9e9</color><color name="aeon_accent">ffffffff</color>'
                 '<color name="aeon_onbar">ff1a1a1a</color><color name="x_panel">ff303030</color>')


class PaletteStyle(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse('<color name="x_panel">FF0A2F5C</color>'), {'x_panel': 'ff0a2f5c'})

    def test_default_palette(self):
        got = style(DEFAULTS, {})
        self.assertEqual((got['ground'], got['ink'], got['bar'], got['barink']), ('ff303030', 'ffffffff', 'ffe9e9e9', 'ff1a1a1a'))

    def test_palette_colours_kept_when_readable(self):
        aqua = parse('<color name="aeon_white">ff14bfaf</color><color name="aeon_accent">ff14bfaf</color>'
                     '<color name="aeon_onbar">ff0d211f</color><color name="x_panel">ff0a2f5c</color>')
        got = style(DEFAULTS, aqua)
        self.assertEqual(got['bar'], 'ff14bfaf')
        self.assertEqual(got['barink'], 'ff0d211f')
        self.assertGreaterEqual(contrast(got['ink'], got['ground']), 4.5)

    def test_dark_ink_on_dark_ground_lifted(self):
        ink = readable('ff202060', 'ff101010')
        self.assertGreaterEqual(contrast(ink, 'ff101010'), 4.5)
        self.assertNotEqual(ink, 'ff202060')

    def test_light_ink_on_light_bar_darkened(self):
        ink = readable('ffdddddd', 'ffeeeeee')
        self.assertGreaterEqual(contrast(ink, 'ffeeeeee'), 4.5)


if __name__ == '__main__':
    unittest.main()
