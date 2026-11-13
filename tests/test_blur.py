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


if __name__ == '__main__':
    unittest.main()
