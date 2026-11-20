import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib import homemenu

OFF = ['off'] * 24


def menu(*items):
    return list(items) + ['off'] * (24 - len(items))


class HomeMenu(unittest.TestCase):
    def test_rows(self):
        self.assertEqual([homemenu.row_id(n) for n in (1, 10, 11, 13, 14, 16, 17, 24)],
                         [9590, 9599, 9613, 9615, 9627, 9629, 9631, 9638])
        self.assertEqual(len(set(homemenu.ROWS.values())), 24)
        self.assertNotIn(homemenu.ADD_ROW, homemenu.ROWS.values())

    def test_custom_number(self):
        self.assertEqual(homemenu.custom_number('custom1'), '1')
        self.assertEqual(homemenu.custom_number('custom10'), '10')
        self.assertEqual(homemenu.custom_number('movies'), '')
        self.assertEqual(len(homemenu.custom_keys()), 10)

    def test_add_after_last(self):
        self.assertEqual(homemenu.add_target(menu('movies', 'tv', 'off', 'music')), 5)
        self.assertEqual(homemenu.add_target(menu('movies')), 2)
        self.assertEqual(homemenu.add_target(OFF), 1)

    def test_add_fills_a_gap_when_the_end_is_full(self):
        full = ['x%d' % n for n in range(1, 25)]
        full[6] = 'off'
        self.assertEqual(homemenu.add_target(full), 7)
        full[6] = ''
        self.assertEqual(homemenu.add_target(full), 7)

    def test_full(self):
        self.assertEqual(homemenu.add_target(['x%d' % n for n in range(1, 25)]), 0)

    def test_count_and_tail(self):
        m = menu('movies', 'off', 'tv')
        self.assertEqual(homemenu.used_count(m), 2)
        self.assertFalse(homemenu.is_tail(m, 2))
        self.assertTrue(homemenu.is_tail(m, 4))
        self.assertTrue(homemenu.is_tail(m, 24))


if __name__ == '__main__':
    unittest.main()
