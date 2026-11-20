# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib import planner


class PlannerFused(unittest.TestCase):
    def test_only_watched(self):
        entries = [{'showtitle': 'Dexter: Resurrection', 'season': 2, 'episode': 3},
                   {'showtitle': 'The Simpsons', 'season': 38, 'episode': 7},
                   {'kind': 'movie', 'title': 'The Hunger Games'},
                   {'kind': 'album', 'title': 'x'}]
        kept = planner.only_watched(entries, ['dexter: resurrection '])
        self.assertEqual([e.get('showtitle') or e.get('title') for e in kept], ['Dexter: Resurrection', 'The Hunger Games', 'x'])
        self.assertEqual(len(planner.only_watched(entries, [])), 2)

    def test_behind(self):
        entry = {'season': 3, 'episode': 5}
        self.assertTrue(planner.behind((3, 1), entry))
        self.assertFalse(planner.behind((3, 5), entry))
        self.assertFalse(planner.behind((4, 1), entry))
        self.assertFalse(planner.behind(None, entry))
        self.assertFalse(planner.behind((1, 1), {'kind': 'movie'}))

    def test_summary(self):
        args = ('1 episode', '{n} episodes', '1 film', '{n} films')
        self.assertEqual(planner.week_summary({'episode': 21, 'movie': 1}, *args), '21 episodes, 1 film')
        self.assertEqual(planner.week_summary({'episode': 1}, *args), '1 episode')
        self.assertEqual(planner.week_summary({}, *args), '')

    def test_rolling_week(self):
        import datetime
        today = datetime.date(2026, 11, 14)
        self.assertEqual(planner.week_dates(today, 0, today.weekday())[0], today)
        self.assertEqual(planner.week_dates(today, 1, today.weekday())[0], datetime.date(2026, 11, 21))


class Earlier(unittest.TestCase):
    def test_step_back_into_the_week(self):
        import datetime
        today = datetime.date(2026, 11, 14)
        monday = datetime.date(2026, 11, 9)
        days = {datetime.date(2026, 11, 10): [1], today: [1], datetime.date(2026, 11, 15): [1]}
        self.assertEqual(planner.step_column(today, today, -1, days), today)
        self.assertEqual(planner.step_column(today, today, -1, days, monday), datetime.date(2026, 11, 10))
        self.assertEqual(planner.step_day(today, monday, -1, days, monday), monday)

    def test_aired(self):
        eps = [{'title': 'A', 'showtitle': 'S', 'season': 1, 'episode': 2, 'firstaired': '2026-11-10', 'art': {'thumb': 't'}},
               {'title': 'B', 'firstaired': ''}]
        got = planner.aired_entries(eps)
        self.assertEqual(len(got), 1)
        self.assertEqual((got[0]['premiered'], got[0]['kind'], got[0]['art']['thumb']), ('2026-11-10', 'episode', 't'))

    def test_earlier_mix(self):
        # 0.3.78: the kept list's entries before today are dropped; the days before today hold the library's episodes
        import datetime
        today = datetime.date(2026, 11, 15)
        kept = [{'showtitle': 'Old', 'premiered': '2026-11-14'}, {'showtitle': 'Now', 'premiered': '2026-11-15'},
                {'showtitle': 'Later', 'premiered': '2026-11-18'}, {'title': 'No date'}]
        aired = [{'showtitle': 'Lib', 'premiered': '2026-11-13'}, {'showtitle': 'Today lib', 'premiered': '2026-11-15'}]
        mixed = planner.earlier_mix(kept, aired, today)
        self.assertEqual([e.get('showtitle') or e.get('title') for e in mixed], ['Now', 'Later', 'No date', 'Lib'])
        days = planner.group(mixed, datetime.date(2026, 11, 9))
        self.assertNotIn(datetime.date(2026, 11, 14), days)
        # stepping back from today skips the day whose list would be empty
        self.assertEqual(planner.step_column(today, today, -1, days, datetime.date(2026, 11, 9)), datetime.date(2026, 11, 13))
        self.assertEqual(planner.step_column(today, datetime.date(2026, 11, 13), -1, days, datetime.date(2026, 11, 9)),
                         datetime.date(2026, 11, 13))
        self.assertEqual(planner.step_column(today, datetime.date(2026, 11, 13), 1, days, datetime.date(2026, 11, 9)), today)
        self.assertEqual(planner.earlier_mix(None, None, today), [])

    def test_aired_cache(self):
        import datetime
        import json
        key = planner.aired_cache_key(datetime.date(2026, 11, 9), datetime.date(2026, 11, 15), '67163')
        self.assertEqual(key, '2026-11-09|2026-11-15|67163')
        raw = json.dumps({'key': key, 'time': 1000, 'entries': [{'premiered': '2026-11-13'}]})
        self.assertEqual(planner.aired_cached(raw, key, 1100), [{'premiered': '2026-11-13'}])
        self.assertIsNone(planner.aired_cached(raw, key, 1000 + 600))        # too old
        self.assertIsNone(planner.aired_cached(raw, key, 900))               # clock went back
        self.assertIsNone(planner.aired_cached(raw, key + 'x', 1100))        # another day, week or library
        self.assertIsNone(planner.aired_cached('', key, 1100))
        self.assertIsNone(planner.aired_cached('{broken', key, 1100))
        self.assertIsNone(planner.aired_cached('[]', key, 1100))


if __name__ == '__main__':
    unittest.main()
