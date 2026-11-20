import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for name in ('xbmc', 'xbmcgui', 'xbmcvfs'):
    sys.modules.setdefault(name, types.ModuleType(name))
import menufile


def menu():
    return [{'label': 'Movies', 'submenu': [{'label': 'Sets', 'path': 'videodb://movies/sets/'}]},
            {'label': 'Power', 'submenu': [{'label': 'Log off', 'path': 'System.LogOff'}, {'label': 'Shut down', 'path': 'Powerdown()'}]}]


class MenuFile(unittest.TestCase):
    def test_added_before_shut_down(self):
        m = menu()
        self.assertTrue(menufile.add_power_item(m, 'Reboot to Android', menufile.ANDROID))
        self.assertEqual([e['path'] for e in m[1]['submenu']], ['System.LogOff', menufile.ANDROID, 'Powerdown()'])
        self.assertTrue(m[1]['submenu'][1]['guid'].startswith('guid-'))
        self.assertEqual(len(m[0]['submenu']), 1)

    def test_not_twice(self):
        m = menu()
        menufile.add_power_item(m, 'Reboot to Android', menufile.ANDROID)
        self.assertFalse(menufile.add_power_item(m, 'Reboot to Android', menufile.ANDROID))
        self.assertEqual(len(m[1]['submenu']), 3)

    def test_no_power_row(self):
        self.assertFalse(menufile.add_power_item([{'label': 'Movies', 'submenu': []}], 'x', 'y'))


class CustomNodes(unittest.TestCase):
    def test_old_file_gets_items_4_to_10(self):
        m = [{'guid': 'guid-aeon0011'}, {'guid': 'guid-aeon0012', 'widgets': [1]}, {'guid': 'guid-aeon0013'}, {'guid': 'guid-aeon0014'}]
        self.assertTrue(menufile.add_custom_nodes(m))
        self.assertEqual([e['guid'] for e in m][4:], ['guid-aeon%04d' % n for n in range(15, 22)])
        self.assertEqual(m[1]['widgets'], [1])
        self.assertEqual(m[-1]['label'], 'Custom item 10')
        self.assertFalse(menufile.add_custom_nodes(m))


if __name__ == '__main__':
    unittest.main()
