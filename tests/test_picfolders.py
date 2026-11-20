# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib import picfolders as pf

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def d(path, label):
    return {'file': path, 'label': label, 'filetype': 'directory', 'mimetype': 'x-directory/normal', 'lastmodified': '2026-11-17 05:57:49'}


def f(path, stamp, mime='image/jpeg'):
    return {'file': path, 'label': path.rsplit('/', 1)[-1], 'filetype': 'file', 'mimetype': mime, 'lastmodified': stamp}


TREE = {
    '/p/': [d('/p/Trips/', 'Trips'), d('/p/Phone/', 'Phone'), f('/p/loose.jpg', '2024-12-24 18:30:00'),
            f('/p/notes.txt', '2026-01-01 00:00:00', 'text/plain')],
    '/p/Trips/': [d('/p/Trips/Lofoten/', 'Lofoten, August'), d('/p/Trips/Empty/', 'Empty')],
    '/p/Trips/Lofoten/': [f('/p/Trips/Lofoten/a.jpg', '2025-08-12 14:28:00'), f('/p/Trips/Lofoten/b.jpg', '2025-08-19 09:00:00'),
                          f('/p/Trips/Lofoten/c.JPG', '2025-08-13 10:00:00', ''), f('/p/Trips/Lofoten/v.mp4', '2025-08-14 12:02:00', 'video/mp4'),
                          f('/p/Trips/Lofoten/d.jpg', '2025-08-15 08:00:00'), f('/p/Trips/Lofoten/e.jpg', '2025-08-16 08:00:00')],
    '/p/Trips/Empty/': [],
    '/p/Phone/': [f('/p/Phone/x.heic', '2026-11-01 08:00:00', ''), f('/p/Phone/y.mov', '2026-11-02 09:00:00', '')],
}


class Kind(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(pf.kind(d('/a/', 'a')), 'folder')
        self.assertEqual(pf.kind(f('/a/b.jpg', '')), 'photo')
        self.assertEqual(pf.kind(f('/a/b.HEIC', '', '')), 'photo')
        self.assertEqual(pf.kind(f('/a/b.mov', '', '')), 'video')
        self.assertEqual(pf.kind(f('/a/b.bin', '', 'video/mp4')), 'video')
        self.assertIsNone(pf.kind(f('/a/b.txt', '', 'text/plain')))

    def test_usable(self):
        self.assertTrue(pf.usable({'file': 'smb://nas/photos/', 'label': 'NAS'}))
        self.assertFalse(pf.usable({'file': 'addons://sources/image/', 'label': 'Picture add-ons'}))
        self.assertFalse(pf.usable({'file': '', 'label': 'x'}))


class Walk(unittest.TestCase):
    def walk(self, **kw):
        return pf.walk(lambda p: TREE.get(p, []), [{'file': '/p/', 'label': 'Photos'}, {'file': 'addons://sources/image/', 'label': 'Picture add-ons'}], **kw)

    def test_newest_first(self):
        names = [x['name'] for x in self.walk()]
        self.assertEqual(names, ['Phone', 'Lofoten, August', 'Photos'])

    def test_counts_dates_parent(self):
        lof = [x for x in self.walk() if x['name'] == 'Lofoten, August'][0]
        self.assertEqual((lof['photos'], lof['videos']), (5, 1))
        self.assertEqual((lof['oldest'], lof['newest']), ('2025-08-12 14:28:00', '2025-08-19 09:00:00'))
        self.assertEqual(lof['parent'], 'Trips')
        self.assertEqual(lof['source'], 'Photos')
        self.assertEqual(lof['pictures'], ['/p/Trips/Lofoten/b.jpg', '/p/Trips/Lofoten/e.jpg', '/p/Trips/Lofoten/d.jpg', '/p/Trips/Lofoten/c.JPG'])

    def test_source_root_and_depth1_parent(self):
        got = {x['name']: x for x in self.walk()}
        self.assertEqual(got['Photos']['depth'], 0)
        self.assertEqual(got['Photos']['photos'], 1)            # the text file is not counted
        self.assertEqual(got['Phone']['parent'], 'Photos')
        self.assertNotIn('Empty', got)

    def test_depth_limit(self):
        names = [x['name'] for x in self.walk(max_depth=1)]
        self.assertNotIn('Lofoten, August', names)

    def test_folder_limit(self):
        self.assertEqual(len(self.walk(max_folders=1)), 1)

    def test_time_limit(self):
        ticks = iter([0, 0, 100, 100, 100, 100])
        got = pf.walk(lambda p: TREE.get(p, []), [{'file': '/p/', 'label': 'Photos'}], clock=lambda: next(ticks))
        self.assertEqual([x['name'] for x in got], ['Photos'])

    def test_unreachable_share(self):
        def boom(path):
            raise IOError('down')
        self.assertEqual(pf.walk(boom, [{'file': 'smb://x/', 'label': 'x'}]), [])


class Dates(unittest.TestCase):
    def test_ranges(self):
        self.assertEqual(pf.date_range('2025-08-12 1', '2025-08-12 2', MONTHS), '12 Aug 2025')
        self.assertEqual(pf.date_range('2025-08-12 1', '2025-08-19 2', MONTHS), '12 – 19 Aug 2025')
        self.assertEqual(pf.date_range('2025-07-28 1', '2025-08-03 2', MONTHS), '28 Jul – 3 Aug 2025')
        self.assertEqual(pf.date_range('2024-12-30 1', '2025-01-02 2', MONTHS), '30 Dec 2024 – 2 Jan 2025')
        self.assertEqual(pf.date_range('', '2025-01-02 2', MONTHS), '2 Jan 2025')
        self.assertEqual(pf.date_range('', '', MONTHS), '')
        self.assertEqual(pf.date_range('2025-08-19 1', '2025-08-12 2', MONTHS), '12 – 19 Aug 2025')


class Cache(unittest.TestCase):
    SRC = [{'file': '/p/', 'label': 'Photos'}, {'file': 'addons://sources/image/', 'label': 'Picture add-ons'}]

    def test_fresh(self):
        cache = {'key': pf.sources_key(self.SRC), 'at': 1000, 'folders': [{'name': 'a'}]}
        self.assertEqual(pf.fresh(cache, self.SRC, 1500), [{'name': 'a'}])
        self.assertIsNone(pf.fresh(cache, self.SRC, 1000 + 901))
        self.assertIsNone(pf.fresh(cache, [{'file': '/q/', 'label': 'Q'}], 1500))
        self.assertIsNone(pf.fresh(None, self.SRC, 1500))
        self.assertIsNone(pf.fresh({'key': pf.sources_key(self.SRC), 'at': 1000}, self.SRC, 1500))


class Spotlight(unittest.TestCase):
    def test_newest(self):
        folders = pf.walk(lambda p: TREE.get(p, []), [{'file': '/p/', 'label': 'Photos'}])
        p = pf.spotlight(folders[1:], MONTHS)                # Lofoten
        self.assertEqual(p['name'], 'Lofoten, August')
        self.assertEqual(p['parent'], 'Trips')
        self.assertEqual((p['photos'], p['videos']), ('5', '1'))
        self.assertEqual(p['dates'], '12 – 19 Aug 2025')
        self.assertEqual(p['bg'], '/p/Trips/Lofoten/b.jpg')
        self.assertEqual(p['thumb4'], '/p/Trips/Lofoten/c.JPG')
        self.assertEqual(p['more'], '2')
        self.assertEqual(p['none'], '')

    def test_videos_only_and_none(self):
        folders = pf.walk(lambda p: TREE.get(p, []), [{'file': '/p/', 'label': 'Photos'}])
        p = pf.spotlight(folders, MONTHS)                    # Phone: one photo, one video, fewer than four thumbs
        self.assertEqual(p['more'], '')
        self.assertEqual(p['thumb2'], '')
        empty = pf.spotlight([], MONTHS)
        self.assertEqual(empty['none'], '1')
        self.assertEqual(empty['name'], '')


if __name__ == '__main__':
    unittest.main()
