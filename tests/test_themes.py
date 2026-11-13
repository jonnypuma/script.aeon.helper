import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from resources.lib.themes import find_theme, folder_of


class Themes(unittest.TestCase):
    def test_finds_theme_in_folder(self):
        have = {'nfs://nas/tv/Show/theme.mp3'}
        self.assertEqual(find_theme('nfs://nas/tv/Show/', have.__contains__), 'nfs://nas/tv/Show/theme.mp3')

    def test_adds_missing_slash(self):
        bs = chr(92)
        base = 'D:' + bs + 'tv' + bs + 'Show'
        have = {base + bs + 'theme.flac'}
        self.assertEqual(find_theme(base, have.__contains__), base + bs + 'theme.flac')

    def test_virtual_paths_have_no_theme(self):
        self.assertEqual(find_theme('videodb://movies/titles/', lambda p: True), '')
        self.assertEqual(find_theme('', lambda p: True), '')

    def test_stack_uses_first_part_folder(self):
        self.assertEqual(folder_of('stack://nfs://nas/m/A/cd1.mkv , nfs://nas/m/A/cd2.mkv'), 'nfs://nas/m/A/')

    def test_none_found(self):
        self.assertEqual(find_theme('nfs://nas/m/A/', lambda p: False), '')


if __name__ == '__main__':
    unittest.main()
