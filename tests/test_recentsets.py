# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib import recentsets


def kodi_set(setid, title, lastplayed, art=None, plot='', playcount=0, file=None):
    """A set as Files.GetDirectory('videodb://movies/sets/') returns it."""
    return {'id': setid, 'label': title, 'title': title, 'lastplayed': lastplayed, 'art': art or {}, 'plot': plot,
            'playcount': playcount, 'type': 'unknown', 'filetype': 'directory',
            'file': file if file is not None else 'videodb://movies/sets/%d/?setid=%d' % (setid, setid)}


class Limit(unittest.TestCase):
    def test_values(self):
        self.assertEqual(recentsets.limit('10'), 10)
        self.assertEqual(recentsets.limit(' 5 '), 5)
        self.assertEqual(recentsets.limit(''), 20)
        self.assertEqual(recentsets.limit(None), 20)
        self.assertEqual(recentsets.limit('0'), 20)
        self.assertEqual(recentsets.limit('-3'), 20)
        self.assertEqual(recentsets.limit('ten'), 20)
        self.assertEqual(recentsets.limit('500'), 100)
        self.assertEqual(recentsets.limit('', default=10), 10)


class Request(unittest.TestCase):
    def test_request(self):
        req = recentsets.request(12)
        self.assertEqual(req['directory'], 'videodb://movies/sets/')
        self.assertEqual(req['sort'], {'method': 'lastplayed', 'order': 'descending'})
        self.assertEqual(req['limits'], {'start': 0, 'end': 12})
        self.assertIn('lastplayed', req['properties'])
        self.assertIn('art', req['properties'])


class SetId(unittest.TestCase):
    def test_id_or_path(self):
        self.assertEqual(recentsets.set_id({'id': 202}), 202)
        self.assertEqual(recentsets.set_id({'id': 0, 'file': 'videodb://movies/sets/4/?setid=4'}), 4)
        self.assertEqual(recentsets.set_id({'file': 'videodb://movies/sets/?setid=567'}), 567)
        self.assertEqual(recentsets.set_id({'id': 'x', 'file': 'videodb://movies/sets/9/'}), 9)
        self.assertEqual(recentsets.set_id({'file': 'videodb://movies/titles/'}), 0)
        self.assertEqual(recentsets.set_id({}), 0)

    def test_path(self):
        self.assertEqual(recentsets.set_path(202), 'videodb://movies/sets/202/')


class Played(unittest.TestCase):
    def test_newest_first_and_never_played_dropped(self):
        art = {'poster': 'p.jpg', 'fanart': 'f.jpg', 'clearlogo': 'l.png'}
        files = [kodi_set(4, 'The Space Odyssey Series', '2026-11-11 00:29:27'),
                 kodi_set(202, 'The Fast and the Furious Collection', '2026-11-14 17:55:21', art, 'Cars.', 0),
                 kodi_set(77, 'Never watched', ''),
                 kodi_set(512, 'Sanjuro Collection', '2026-11-09 13:05:10', playcount=1)]
        found = recentsets.played(files, 10)
        self.assertEqual([f['setid'] for f in found], [202, 4, 512])
        first = found[0]
        self.assertEqual(first['label'], 'The Fast and the Furious Collection')
        self.assertEqual(first['path'], 'videodb://movies/sets/202/')
        self.assertEqual(first['art'], art)
        self.assertEqual(first['plot'], 'Cars.')
        self.assertEqual(first['lastplayed'], '2026-11-14 17:55:21')
        self.assertEqual((first['playcount'], found[2]['playcount']), (0, 1))

    def test_count(self):
        files = [kodi_set(n, 'Set %d' % n, '2026-01-%02d 10:00:00' % n) for n in range(1, 9)]
        self.assertEqual([f['setid'] for f in recentsets.played(files, 3)], [8, 7, 6])

    def test_bad_items(self):
        files = [{'label': 'No id', 'lastplayed': '2026-01-01 00:00:00', 'file': 'videodb://movies/titles/'},
                 kodi_set(3, 'Twice', '2026-02-02 00:00:00'), kodi_set(3, 'Twice', '2026-02-02 00:00:00'),
                 {'id': 5, 'lastplayed': '2026-03-03 00:00:00'}]
        found = recentsets.played(files, 10)
        self.assertEqual([f['setid'] for f in found], [5, 3])
        self.assertEqual(found[0]['label'], '')
        self.assertEqual(found[0]['path'], 'videodb://movies/sets/5/')

    def test_equal_times_stable(self):
        files = [kodi_set(3, 'A', '2026-05-05 10:00:00'), kodi_set(8, 'B', '2026-05-05 10:00:00')]
        self.assertEqual([f['setid'] for f in recentsets.played(files, 5)], [8, 3])

    def test_empty(self):
        self.assertEqual(recentsets.played(None, 5), [])
        self.assertEqual(recentsets.played([], 5), [])


if __name__ == '__main__':
    unittest.main()
