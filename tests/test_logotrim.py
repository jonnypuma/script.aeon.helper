# -*- coding: utf-8 -*-
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import logotrim

try:
    from PIL import Image
except ImportError:
    Image = None


class TestLogoTrim(unittest.TestCase):
    def test_cache_name_is_stable_and_differs(self):
        self.assertEqual(logotrim.cache_name('nfs://a/logo.png'), logotrim.cache_name('nfs://a/logo.png'))
        self.assertNotEqual(logotrim.cache_name('nfs://a/logo.png'), logotrim.cache_name('nfs://b/logo.png'))
        self.assertTrue(logotrim.cache_name(u'nfs://a/l\xf8go.png').endswith('.png'))

    def test_content_box(self):
        self.assertEqual(logotrim.content_box((800, 310), (9, 55, 794, 258)), (9, 55, 794, 258))
        self.assertIsNone(logotrim.content_box((800, 310), (0, 0, 800, 310)))
        self.assertIsNone(logotrim.content_box((800, 310), None))
        self.assertIsNone(logotrim.content_box((800, 310), (10, 10, 12, 12)))

    def test_bad_data(self):
        self.assertEqual(logotrim.trim(b'not a picture'), b'')

    @unittest.skipIf(Image is None, 'Pillow not installed')
    def test_trim_removes_border(self):
        image = Image.new('RGBA', (800, 310), (0, 0, 0, 0))
        image.paste((255, 255, 255, 255), (9, 55, 794, 258))
        data = io.BytesIO()
        image.save(data, 'PNG')
        trimmed = Image.open(io.BytesIO(logotrim.trim(data.getvalue())))
        self.assertEqual(trimmed.size, (785, 203))

    @unittest.skipIf(Image is None, 'Pillow not installed')
    def test_large_logo_is_scaled(self):
        image = Image.new('RGBA', (1600, 400), (255, 255, 255, 255))
        data = io.BytesIO()
        image.save(data, 'PNG')
        trimmed = Image.open(io.BytesIO(logotrim.trim(data.getvalue())))
        self.assertEqual(trimmed.size, (800, 200))


if __name__ == '__main__':
    unittest.main()
