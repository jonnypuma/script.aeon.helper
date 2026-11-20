# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resources.lib.sysinfo import major, device, os_line, screen, cpu_average, grouped


class SysInfo(unittest.TestCase):
    def test_major(self):
        self.assertEqual(major('22.0-RC2'), ('22', 'RC2'))
        self.assertEqual(major('21.2'), ('21', ''))
        self.assertEqual(major('22.0-ALPHA1'), ('22', 'ALPHA1'))
        self.assertEqual(major(''), ('', ''))
        self.assertEqual(major(None), ('', ''))

    def test_device(self):
        self.assertEqual(device('Kodi (CoreELECAM9Pro)'), 'CoreELECAM9Pro')
        self.assertEqual(device('Living room'), 'Living room')
        self.assertEqual(device(''), '')

    def test_os_coreelec(self):
        self.assertEqual(os_line('CoreELEC (official): 22.0-Piers_nightly_20261113'),
                         ('CoreELEC', 'CoreELEC 22 Piers nightly, 13 November'))

    def test_os_months(self):
        months = ['m%d' % i for i in range(1, 13)]
        self.assertEqual(os_line('CoreELEC (official): 22.0-Piers_nightly_20260105', months)[1], 'CoreELEC 22 Piers nightly, 5 m1')

    def test_os_release(self):
        self.assertEqual(os_line('LibreELEC (official): 12.0.1'), ('LibreELEC', 'LibreELEC 12.0.1'))
        self.assertEqual(os_line('CoreELEC (official): 21.0-Omega'), ('CoreELEC', 'CoreELEC 21 Omega'))

    def test_os_other(self):
        text = 'Windows 11, 64-bit Home (version 10.0 build 26200)'
        self.assertEqual(os_line(text), ('Windows', text))
        self.assertEqual(os_line(''), ('', ''))

    def test_screen(self):
        self.assertEqual(screen('3840x2160 @ 24.00 Hz - Full screen'), u'2160p · 24 Hz')
        self.assertEqual(screen('1920x1080 @ 23.98 Hz - Full screen'), u'1080p · 23.98 Hz')
        self.assertEqual(screen('1920x1080 @ 59.94 Hz - Windowed'), u'1080p · 59.94 Hz')
        self.assertEqual(screen('1280x720'), '720p')
        self.assertEqual(screen('Busy'), 'Busy')

    def test_cpu(self):
        self.assertEqual(cpu_average('#0:  18% #1: 100% #2:  21% #3:  14%'), '38')
        self.assertEqual(cpu_average('13%'), '13')
        self.assertEqual(cpu_average(''), '')

    def test_grouped(self):
        self.assertEqual(grouped(6123), '6,123')
        self.assertEqual(grouped('335972', 'de'), '335.972')
        self.assertEqual(grouped(67165, 'fr'), u'67 165')
        self.assertEqual(grouped(12, 'nl'), '12')
        self.assertEqual(grouped('x'), 'x')


if __name__ == '__main__':
    unittest.main()
