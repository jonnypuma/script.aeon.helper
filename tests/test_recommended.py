import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import recommended  # noqa: E402


class RecommendedTest(unittest.TestCase):
    def test_repos_known(self):
        for aid, _n, _s, repo in recommended.ADDONS:
            self.assertTrue(repo is None or repo in recommended.REPOS, aid)
        self.assertEqual(len(set(a[0] for a in recommended.ADDONS)), len(recommended.ADDONS))

    def test_rows(self):
        have = {'service.skippy', 'repository.jamal2362'}
        rows = dict((r[0], r) for r in recommended.rows(lambda a: a in have, lambda a: '1.0'))
        self.assertTrue(rows['service.skippy'][3])
        self.assertEqual(rows['service.skippy'][4], '1.0')
        self.assertEqual(rows['service.trickplay'][5], 'repository.skippyrepo')   # repo missing: install it first
        self.assertIsNone(rows['script.tinyppi'][5])                             # repo there
        self.assertIsNone(rows['plugin.video.themoviedb.helper'][5])             # Kodi repository
        self.assertEqual(recommended.count(lambda a: a in have), (1, len(recommended.ADDONS)))

    def test_zip_ok(self):
        r = 'repository.jamal2362'
        self.assertTrue(recommended.zip_ok([r + '/', r + '/addon.xml', r + '/icon.png'], r))
        self.assertFalse(recommended.zip_ok([r + '/addon.xml', 'other/addon.xml'], r))
        self.assertFalse(recommended.zip_ok([r + '/../../evil.py'], r))


if __name__ == '__main__':
    unittest.main()


class WaveformTest(unittest.TestCase):
    def test_mapping(self):
        w = recommended.waveform_id
        self.assertEqual(w('aarch64', 'Linux'), 'visualization.aeonwave.linux-arm64')
        self.assertEqual(w('armv7l', 'Linux'), 'visualization.aeonwave.linux-armv7')
        self.assertEqual(w('armv7', 'Linux'), 'visualization.aeonwave.linux-armv7')
        self.assertEqual(w('x86_64', 'Linux'), 'visualization.aeonwave.linux-x86_64')
        self.assertEqual(w('AMD64', 'Windows'), 'visualization.aeonwave.windows-x64')
        self.assertIsNone(w('x86', 'Windows'))
        self.assertIsNone(w('aarch64', 'Linux', android=True))
        self.assertIsNone(w('arm64', 'Darwin'))
        self.assertIsNone(w('mips', 'Linux'))

    def test_listed(self):
        items = recommended.listed('aarch64', 'Linux')
        ids = [a[0] for a in items]
        self.assertIn('visualization.aeonwave.linux-arm64', ids)
        self.assertEqual(ids.index('visualization.aeonwave.linux-arm64'), ids.index('screensaver.aeon.fuse') + 1)
        self.assertEqual(dict((a[0], a[3]) for a in items)['visualization.aeonwave.linux-arm64'], 'repository.skippyrepo')
        self.assertEqual(len(recommended.listed('aarch64', 'Linux', android=True)), len(recommended.ADDONS))
        self.assertEqual(recommended.count(lambda a: False, items), (0, len(recommended.ADDONS) + 1))
