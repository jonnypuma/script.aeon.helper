# -*- coding: utf-8 -*-
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import blur

try:
    from PIL import Image
except ImportError:
    Image = None


class TestBlur(unittest.TestCase):
    def test_cache_name(self):
        self.assertEqual(blur.cache_name('http://a/f.jpg'), blur.cache_name('http://a/f.jpg'))
        self.assertNotEqual(blur.cache_name('http://a/f.jpg'), blur.cache_name('http://b/f.jpg'))
        self.assertTrue(blur.cache_name(u'nfs://a/f\xf8.jpg').endswith('.jpg'))

    def test_radius_steps(self):
        # 0.3.104 Expert settings: Panel blur / Fanart blur
        self.assertEqual(blur.panel_radius(''), blur.RADIUS)
        self.assertEqual(blur.panel_radius('nonsense'), blur.RADIUS)
        self.assertIsNone(blur.panel_radius('off'))
        self.assertLess(blur.panel_radius('light'), blur.RADIUS)
        self.assertGreater(blur.panel_radius('strong'), blur.RADIUS)
        # 0.3.111: Off, -2 .. +2, '' / z = 0 (the old Light) is the default; the old steps still read
        self.assertIsNone(blur.fanart_radius('off'))
        self.assertEqual([blur.fanart_radius(s) for s in ('m2', 'm1', '', 'p1', 'p2')], [1, 2, 4, 9, 16])
        self.assertEqual(blur.fanart_radius('z'), blur.fanart_radius(''))
        self.assertEqual(blur.fanart_radius('nonsense'), 4)
        self.assertEqual(sorted(blur.fanart_radius(s) for s in ('light', 'medium', 'strong')), [4, 9, 16])
        # the default radius keeps the old cache names; others get their own
        self.assertEqual(blur.cache_name('x', blur.RADIUS), blur.cache_name('x'))
        self.assertNotEqual(blur.cache_name('x', 8), blur.cache_name('x'))
        self.assertTrue(blur.cache_name('x', 8).endswith('_r8.jpg'))

    def test_cover_box(self):
        self.assertEqual(blur.cover_box((1920, 1080)), (0, 0, 1920, 1080))
        self.assertEqual(blur.cover_box((2000, 1000)), (111, 0, 1889, 1000))     # wide: sides cut
        self.assertEqual(blur.cover_box((1000, 1000)), (0, 219, 1000, 781))      # square: top and bottom cut
        self.assertIsNone(blur.cover_box((0, 10)))

    def test_bad_data(self):
        self.assertEqual(blur.make(b'not a picture'), b'')

    @unittest.skipIf(Image is None, 'Pillow not installed')
    def test_make(self):
        src = Image.new('RGB', (1280, 720), (200, 30, 30))
        for x in range(0, 1280, 40):
            src.paste((20, 20, 220), (x, 0, x + 20, 720))
        data = io.BytesIO()
        src.save(data, 'JPEG')
        out = Image.open(io.BytesIO(blur.make(data.getvalue())))
        self.assertEqual(out.size, blur.SIZE)
        self.assertEqual(out.format, 'JPEG')
        # stripes 20 px wide are blurred away: neighbouring pixels are close in colour
        a, b = out.getpixel((100, 180)), out.getpixel((106, 180))
        self.assertLess(sum(abs(p - q) for p, q in zip(a, b)), 60)



class MenuRadiusTest(unittest.TestCase):
    """0.3.110: the menus' blurred backdrop - Fused Glass Frost at the default radius, Aeon Glass per Panel blur step"""

    def test_frost_default(self):
        self.assertEqual(blur.menu_radius(True, ''), blur.RADIUS)
        self.assertEqual(blur.menu_radius(True, 'strong'), blur.RADIUS)

    def test_aeon_glass_steps(self):
        self.assertIsNone(blur.menu_radius(False, ''))
        self.assertEqual(blur.menu_radius(False, 'light'), 6)
        self.assertEqual(blur.menu_radius(False, 'medium'), blur.RADIUS)
        self.assertEqual(blur.menu_radius(False, 'strong'), 24)
        self.assertIsNone(blur.menu_radius(False, 'nonsense'))

    def test_names_differ_per_radius(self):
        self.assertNotEqual(blur.cache_name('x.jpg', 6), blur.cache_name('x.jpg', 24))
        self.assertEqual(blur.cache_name('x.jpg', blur.RADIUS), blur.cache_name('x.jpg'))


class FanblurMigrationTest(unittest.TestCase):
    """0.3.111: the old Library fanart blur steps move to the new ones; a view's 0 is z (empty follows Skin settings)"""

    def test_global(self):
        self.assertEqual(blur.fanblur_new('light'), '')
        self.assertEqual(blur.fanblur_new('medium'), 'p1')
        self.assertEqual(blur.fanblur_new('strong'), 'p2')

    def test_view(self):
        self.assertEqual(blur.fanblur_new('light', view=True), 'z')
        self.assertEqual(blur.fanblur_new('strong', view=True), 'p2')

    def test_new_values_stay(self):
        for v in ('', 'off', 'm2', 'm1', 'z', 'p1', 'p2'):
            self.assertIsNone(blur.fanblur_new(v))

if __name__ == '__main__':
    unittest.main()
