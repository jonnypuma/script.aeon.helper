# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib.headline import bold_last


class TestHeadline(unittest.TestCase):
    def test_last_word_bold(self):
        self.assertEqual(bold_last('Random shows'), 'Random [B]shows[/B]')
        self.assertEqual(bold_last('Recently added episodes'), 'Recently added [B]episodes[/B]')
        self.assertEqual(bold_last('Kürzlich hinzugefügte Serien'), 'Kürzlich hinzugefügte [B]Serien[/B]')

    def test_one_word_and_empty(self):
        self.assertEqual(bold_last('Films'), '[B]Films[/B]')
        self.assertEqual(bold_last(''), '')
        self.assertEqual(bold_last(None), '')

    def test_tags_and_spaces_dropped(self):
        self.assertEqual(bold_last('[COLOR red]New[/COLOR]  [B]films[/B] '), 'New [B]films[/B]')
        self.assertEqual(bold_last('ランダムな番組'), '[B]ランダムな番組[/B]')


if __name__ == '__main__':
    unittest.main()
