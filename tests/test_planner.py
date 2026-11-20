import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib.planner import headings, due, merge, next_refresh, refresh_choice

WORDS = {'today': 'Today', 'tomorrow': 'Tomorrow', 'weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
TODAY = datetime.date(2026, 11, 11)          # a Wednesday


class Planner(unittest.TestCase):
    def test_grouped_by_day(self):
        got = headings(['2026-11-11', '2026-11-11', '2026-11-12', '2026-11-14', '2026-11-14', '2026-12-01'], TODAY, WORDS, MONTHS)
        self.assertEqual(got, [('Today', '11 November'), ('', ''), ('Tomorrow', '12 November'), ('Saturday', '14 November'), ('', ''), ('Tuesday', '1 December')])

    def test_bad_date(self):
        self.assertEqual(headings(['soon'], TODAY, WORDS, MONTHS), [('', 'soon')])
        self.assertEqual(headings([], TODAY, WORDS, MONTHS), [])


class WeekKinds(unittest.TestCase):
    def test_kinds_apart(self):
        from resources.lib import planner as pl
        today = datetime.date(2026, 11, 13)
        entries = [{'premiered': '2026-11-13'}, {'premiered': '2026-11-13', 'kind': 'movie'},
                   {'premiered': '2026-11-15', 'kind': 'album'}, {'premiered': '2026-11-15', 'kind': 'episode'},
                   {'premiered': '2026-11-25'}, {'premiered': ''}]
        got = pl.week_kinds(entries, today)
        self.assertEqual(len(got), 7)
        self.assertEqual(got[0], (today, 1, 1, 0))
        self.assertEqual(got[1][1:], (0, 0, 0))
        self.assertEqual(got[2][1:], (1, 0, 1))


if __name__ == '__main__':
    unittest.main()


from resources.lib import planner as P


def D(text):
    return datetime.datetime.strptime(text, '%Y-%m-%d').date()


class Calendar(unittest.TestCase):
    def test_week_dates_monday_start(self):
        week = P.week_dates(TODAY, 0)
        self.assertEqual(week[0], D('2026-11-09'))
        self.assertEqual(week[6], D('2026-11-15'))
        self.assertEqual(P.week_dates(TODAY, 1)[0], D('2026-11-16'))

    def test_week_dates_other_start(self):
        self.assertEqual(P.week_dates(TODAY, 0, 6)[0], D('2026-11-08'))       # week starts on Sunday
        self.assertEqual(P.week_dates(TODAY, 0, 2)[0], D('2026-11-11'))       # starts on Wednesday = today
        self.assertEqual(P.week_dates(TODAY, 0, 3)[0], D('2026-11-05'))       # starts on Thursday

    def test_locate(self):
        self.assertEqual(P.locate(TODAY, TODAY), (0, 2))
        self.assertEqual(P.locate(TODAY, D('2026-11-16')), (1, 0))
        self.assertEqual(P.locate(TODAY, D('2026-11-15'), 6), (1, 0))

    def test_day_title(self):
        self.assertEqual(P.day_title(TODAY, WORDS['weekdays'], MONTHS), 'Wednesday 11 Nov 2026')

    def test_group_drops_past_and_sorts(self):
        entries = [{'premiered': '2026-11-10', 'showtitle': 'Old'}, {'premiered': '2026-11-11', 'showtitle': 'b'},
                   {'premiered': '2026-11-11', 'showtitle': 'A'}, {'premiered': '2026-11-11', 'showtitle': 'z', 'time': '18:00'},
                   {'premiered': 'soon', 'showtitle': 'x'}, {'premiered': '2026-11-13', 'title': 'Film'}]
        days = P.group(entries, TODAY)
        self.assertEqual(sorted(days), [D('2026-11-11'), D('2026-11-13')])
        self.assertEqual([e['showtitle'] for e in days[TODAY]], ['z', 'A', 'b'])

    def test_step_day_bounds(self):
        days = {TODAY: [1], D('2026-11-14'): [1]}
        self.assertEqual(P.step_day(TODAY, TODAY, -1, days), TODAY)                    # never before today
        self.assertEqual(P.step_day(TODAY, TODAY, 1, days), D('2026-11-12'))            # empty days are shown too
        self.assertEqual(P.step_day(TODAY, D('2026-11-14'), 1, days), D('2026-11-14'))  # nothing planned later
        self.assertEqual(P.step_day(TODAY, TODAY, 1, {}), TODAY)

    def test_step_column_skips_empty_days_and_weeks(self):
        days = {TODAY: [1], D('2026-11-14'): [1], D('2026-11-24'): [1]}
        self.assertEqual(P.step_column(TODAY, TODAY, 1, days), D('2026-11-14'))
        self.assertEqual(P.step_column(TODAY, D('2026-11-14'), 1, days), D('2026-11-24'))    # into a later week
        self.assertEqual(P.step_column(TODAY, D('2026-11-24'), 1, days), D('2026-11-24'))
        self.assertEqual(P.step_column(TODAY, D('2026-11-14'), -1, days), TODAY)
        self.assertEqual(P.step_column(TODAY, TODAY, -1, days), TODAY)

    def test_first_planned(self):
        self.assertEqual(P.first_planned(TODAY, {D('2026-11-13'): [1]}), D('2026-11-13'))
        self.assertEqual(P.first_planned(TODAY, {}), TODAY)


DAY = 86400.0


class KeptList(unittest.TestCase):
    def test_interval(self):
        kept = {'time': 1000.0, 'episodes': [1], 'movies': [1]}
        self.assertFalse(due(kept, '', 1000 + 13 * DAY))
        self.assertTrue(due(kept, '', 1000 + 15 * DAY))
        self.assertTrue(due(kept, 'daily', 1000 + 1.5 * DAY))
        self.assertFalse(due(kept, 'weekly', 1000 + 6 * DAY))
        self.assertFalse(due(kept, 'monthly', 1000 + 29 * DAY))
        self.assertTrue(due(kept, 'monthly', 1000 + 31 * DAY))
        self.assertTrue(due(kept, 'nonsense', 1000 + 15 * DAY))

    def test_kept_without_episodes_is_retried(self):
        wiped = {'time': 1000.0, 'episodes': [], 'movies': ['m']}
        self.assertFalse(due(wiped, '', 1000 + 3600))
        self.assertTrue(due(wiped, '', 1000 + 7 * 3600))

    def test_nothing_kept(self):
        self.assertTrue(due({}, '', 5.0))

    def test_empty_read_keeps_the_list(self):
        old = {'time': 100.0, 'episodes': ['a', 'b'], 'movies': ['m']}
        got = merge(old, [], ['n'], 900.0)
        self.assertEqual(got['episodes'], ['a', 'b'])
        self.assertEqual(got['movies'], ['n'])
        self.assertTrue(got['partial'])
        self.assertEqual(got['time'], 100.0)
        self.assertEqual(got['tried'], 900.0)
        # tried again after six hours, not every half hour
        self.assertFalse(due(got, '', 900.0 + 3600))
        self.assertTrue(due(got, '', 900.0 + 7 * 3600))

    def test_full_read_replaces(self):
        got = merge({'time': 1.0, 'episodes': ['old'], 'movies': ['old']}, ['e'], ['m'], 50.0)
        self.assertEqual((got['episodes'], got['movies'], got['time']), (['e'], ['m'], 50.0))
        self.assertNotIn('partial', got)

    def test_failed_reads_back_off(self):
        data = {'time': 0.0, 'episodes': [], 'movies': []}
        first = merge(data, [], ['m'], 100.0)
        self.assertEqual(first['failures'], 1)
        second = merge(first, [], ['m'], 200.0)
        self.assertEqual(second['failures'], 2)
        self.assertFalse(due(second, '', 200.0 + 7 * 3600))      # 12 h after the second failure
        self.assertTrue(due(second, '', 200.0 + 13 * 3600))
        ok = merge(second, ['e'], ['m'], 300.0)
        self.assertNotIn('failures', ok)

    def test_cycle(self):
        self.assertEqual(next_refresh(''), 'monthly')
        self.assertEqual(next_refresh('monthly'), 'daily')
        self.assertEqual(next_refresh('daily'), 'weekly')
        self.assertEqual(next_refresh('weekly'), '')
        self.assertEqual(refresh_choice('x'), '')


class TestWeekCounts(unittest.TestCase):
    def test_counts_per_day_from_today(self):
        import datetime
        from resources.lib import planner as pl
        today = datetime.date(2026, 11, 13)
        entries = [{'premiered': '2026-11-13'}, {'premiered': '2026-11-13'}, {'premiered': '2026-11-15'},
                   {'premiered': '2026-11-25'}, {'premiered': 'bad'}]
        got = pl.week_counts(entries, today)
        self.assertEqual(len(got), 7)
        self.assertEqual(got[0], (today, 2))
        self.assertEqual(got[1][1], 0)
        self.assertEqual(got[2], (datetime.date(2026, 11, 15), 1))
        self.assertEqual(sum(c for _, c in got), 3)


class Placeholders(unittest.TestCase):
    def test_text_or_empty(self):
        from resources.lib.planner import text_or_empty
        self.assertEqual(text_or_empty('None'), '')
        self.assertEqual(text_or_empty(None), '')
        self.assertEqual(text_or_empty(' TBA '), '')
        self.assertEqual(text_or_empty('A real plot.'), 'A real plot.')

    def test_real_episode_title(self):
        from resources.lib.planner import real_episode_title
        for generic in ('Episode 2', 'episode 12', 'Folge 3', 'Aflevering 4', '#5', 'TBA', 'None', '7'):
            self.assertEqual(real_episode_title(generic), '', generic)
        self.assertEqual(real_episode_title('The Fight Rages On'), 'The Fight Rages On')
        self.assertEqual(real_episode_title('Episode 2: The Return'), 'Episode 2: The Return')
