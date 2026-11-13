# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import memtrim


class TestMemTrim(unittest.TestCase):
    def test_trim_is_safe_everywhere(self):
        # Linux: 0 or 1; elsewhere (Windows / macOS) there is nothing to call: None
        result = memtrim.trim()
        if sys.platform.startswith('linux'):
            self.assertIn(result, (0, 1))
        else:
            self.assertIsNone(result)
            self.assertFalse(memtrim.available())

    def test_meminfo_reads_total_and_available(self):
        import tempfile
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as handle:
            handle.write('MemTotal:        3787776 kB\nMemFree:  100 kB\nMemAvailable:    2293760 kB\n')
        try:
            self.assertEqual(memtrim.meminfo_mb(handle.name), (3699, 2240))
        finally:
            os.remove(handle.name)
        self.assertEqual(memtrim.meminfo_mb('/no/such/file'), (None, None))

    def test_settings_defaults_and_limits(self):
        self.assertEqual(memtrim.settings('', '', ''), ('free', 5, 1024))
        self.assertEqual(memtrim.settings('idle', '15', '2048'), ('idle', 15, 2048))
        self.assertEqual(memtrim.settings('IDLE', '1', '100'), ('idle', 2, memtrim.EMERGENCY_MB))
        self.assertEqual(memtrim.settings('free', '99', 'x'), ('free', 30, 1024))

    def test_free_mode_keeps_the_minimum_free(self):
        d = memtrim.decide
        self.assertIsNone(d('free', 1700, 1000, 0, None, paused=True))                 # plenty free
        self.assertIsNone(d('free', 1200, 1000, 0, None, paused=False))                # close, keys in use: wait
        self.assertEqual(d('free', 1200, 1000, 0, None, paused=True), 'now')           # close, in a pause
        self.assertIsNone(d('free', 1200, 1000, 0, None, paused=True, video=True))     # close, but a video plays
        self.assertEqual(d('free', 1000, 1000, 0, None), 'now')                        # at the line: at once
        self.assertEqual(d('free', 1900, 1000, 0, None, free_mb=2048), 'now')          # 2 GB chosen
        self.assertIsNone(d('free', 1900, 1000, 0, None, free_mb=512))

    def test_idle_mode_waits_for_the_rest(self):
        d = memtrim.decide
        self.assertIsNone(d('idle', 3000, 1000, 0, None, rested=False))
        self.assertEqual(d('idle', 3000, 1000, 0, None, rested=True), 'now')
        self.assertIsNone(d('idle', 3000, 1000, 0, None, rested=True, video=True))
        self.assertEqual(d('idle', 300, 1000, 0, None, rested=False), 'now')           # emergency

    def test_video_only_a_lasting_shortage(self):
        d = memtrim.decide
        self.assertIsNone(d('free', 1200, 1000, 0, None, paused=True, video=True))                # above the minimum
        self.assertIsNone(d('free', 900, 1000, 0, None, video=True, low_since=995))               # under it for 5 s
        self.assertEqual(d('free', 900, 1000, 0, None, video=True, low_since=985), 'now')        # for 15 s
        self.assertIsNone(d('free', 900, 1000, 0, None, video=True, low_since=None))
        self.assertIsNone(d('idle', 3000, 1000, 0, None, rested=True, video=True))
        self.assertEqual(d('idle', 300, 1000, 0, None, video=True), 'now')                        # emergency

    def test_video_edges(self):
        e = memtrim.video_edge
        self.assertEqual(e(False, True, 1000, 0), 'start')
        self.assertEqual(e(True, False, 1000, 0), 'stop')
        self.assertIsNone(e(True, True, 1000, 0))
        self.assertIsNone(e(False, True, 1000, 998))      # a trim 2 s ago

    def test_decide_cooldowns(self):
        d = memtrim.decide
        self.assertIsNone(d('free', 900, 1000, 990, 800))                 # 10 s after the last trim
        self.assertEqual(d('free', 900, 1000, 970, 800), 'now')
        self.assertIsNone(d('free', 900, 1000, 950, 10))                  # it gave nothing back 50 s ago
        self.assertEqual(d('free', 900, 1000, 850, 10), 'now')
        self.assertEqual(d('free', 300, 1000, 950, 10), 'now')            # emergency beats the stale wait
        self.assertIsNone(d('free', None, 1000, 0, None))                 # not Linux


if __name__ == '__main__':
    unittest.main()
