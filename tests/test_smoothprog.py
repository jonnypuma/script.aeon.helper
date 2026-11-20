# -*- coding: utf-8 -*-
"""smoothprog.SmoothProgress.follow against stand-in xbmc / xbmcgui modules: a scripted player time, a recording
progress control and a monitor whose waits move a fake clock."""
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


class World(object):
    """What the stand-ins read and record."""

    def __init__(self, times, total=240.0, fps='60.00', mode='3840x2160 @ 59.94 - Full Screen', rate='',
                 paused_from=None, stop_after=None, control=True):
        self.times = list(times)       # player time for each update, in order
        self.total = total
        self.labels = {'System.FPS': fps, 'System.ScreenMode': mode, 'Skin.String(aeon.smoothprogress.rate)': rate}
        self.paused_from = paused_from  # update index from which Player.Paused is true
        self.stop_after = stop_after    # update count after which the window counts as closed
        self.control = control
        self.updates = 0
        self.percents = []
        self.waits = []
        self.props = {}
        self.prop_history = []
        self.clock = 0.0


def install(world):
    xbmc = types.ModuleType('xbmc')
    xbmc.LOGINFO = 1
    xbmc.log = lambda text, level=0: None
    xbmc.getSkinDir = lambda: 'skin.aeon.fuse'
    xbmc.getInfoLabel = lambda label: world.labels.get(label, '')

    def cond(text):
        if text == 'Player.Paused':
            return world.paused_from is not None and world.updates >= world.paused_from
        return world.stop_after is None or world.updates < world.stop_after
    xbmc.getCondVisibility = cond

    class Player(object):
        def getTotalTime(self):
            if not world.times:
                raise RuntimeError('not playing')
            return world.total

        def getTime(self):
            if not world.times:
                raise RuntimeError('not playing')
            return world.times.pop(0)

    class Monitor(object):
        def waitForAbort(self, seconds):
            world.waits.append(seconds)
            world.clock += seconds
            return False
    xbmc.Player = Player
    xbmc.Monitor = Monitor

    xbmcgui = types.ModuleType('xbmcgui')

    class Control(object):
        def setPercent(self, value):
            world.percents.append(value)

    class Window(object):
        def __init__(self, wid):
            self.wid = wid

        def getControl(self, cid):
            if not world.control:
                raise RuntimeError('Non-Existent Control %d' % cid)
            world.updates += 1
            return Control()

        def setProperty(self, key, value):
            world.props[key] = value
            world.prop_history.append((key, value))

        def clearProperty(self, key):
            world.props.pop(key, None)
            world.prop_history.append((key, None))
    xbmcgui.Window = Window
    sys.modules['xbmc'] = xbmc
    sys.modules['xbmcgui'] = xbmcgui
    sys.modules.pop('smoothprog', None)
    import smoothprog
    smoothprog.time.monotonic = lambda: world.clock
    return smoothprog


class TestSmoothProgress(unittest.TestCase):
    def tearDown(self):
        for name in ('xbmc', 'xbmcgui', 'smoothprog'):
            sys.modules.pop(name, None)

    def run_world(self, world):
        smoothprog = install(world)
        smoothprog.SmoothProgress().follow()
        return smoothprog

    def test_percent_follows_the_player(self):
        world = World([0.0, 12.0, 120.0, 239.0])
        self.run_world(world)
        self.assertEqual([round(p, 3) for p in world.percents], [0.0, 5.0, 50.0, 99.583])

    def test_property_set_after_first_update_and_cleared_at_the_end(self):
        world = World([10.0, 10.1])
        self.run_world(world)
        self.assertEqual(world.prop_history[0], ('aeon.smoothprog', '1'))
        self.assertEqual(world.prop_history[-1], ('aeon.smoothprog', None))
        self.assertNotIn('aeon.smoothprog', world.props)

    def test_small_step_back_is_held(self):
        # Kodi's time wobbles while paused: 100.40 -> 100.37 must not move the fill back
        world = World([100.40, 100.37, 100.39, 100.41])
        self.run_world(world)
        self.assertEqual([round(p * 2.4, 2) for p in world.percents], [100.40, 100.40, 100.40, 100.41])

    def test_seek_back_and_next_song_snap(self):
        world = World([100.0, 99.0, 0.2])
        self.run_world(world)
        self.assertEqual([round(p * 2.4, 2) for p in world.percents], [100.0, 99.0, 0.2])

    def test_rate_screen_follows_kodis_frames(self):
        world = World([1.0, 1.1, 1.2], fps='34.72')
        self.run_world(world)
        self.assertAlmostEqual(world.waits[0], 1.0 / 34.72)

    def test_rate_screen_falls_back_to_the_refresh_rate(self):
        for fps in ('', '3.5'):
            world = World([1.0, 1.1], fps=fps)
            self.run_world(world)
            self.assertAlmostEqual(world.waits[0], 1.0 / 59.94)
        world = World([1.0, 1.1], fps='', mode='')
        self.run_world(world)
        self.assertAlmostEqual(world.waits[0], 1.0 / 60)

    def test_rate_screen_is_capped(self):
        world = World([1.0, 1.1], fps='240.0')
        self.run_world(world)
        self.assertAlmostEqual(world.waits[0], 1.0 / 120)

    def test_fixed_rates(self):
        for rate in ('10', '25', '30', '60'):
            world = World([1.0, 1.1, 1.2], rate=rate, fps='50.0')
            self.run_world(world)
            self.assertAlmostEqual(world.waits[0], 1.0 / float(rate))
            self.assertAlmostEqual(world.waits[1], 1.0 / float(rate))

    def test_unknown_rate_means_screen(self):
        world = World([1.0, 1.1], rate='15', fps='50.0')
        self.run_world(world)
        self.assertAlmostEqual(world.waits[0], 1.0 / 50)

    def test_paused_slows_down(self):
        world = World([5.0, 5.0, 5.0], paused_from=0)
        self.run_world(world)
        self.assertEqual(world.waits[:2], [0.25, 0.25])

    def test_stream_without_length_leaves_the_stock_fill(self):
        world = World([5.0, 6.0], total=0.0)
        self.run_world(world)
        self.assertEqual(world.percents, [])
        self.assertNotIn(('aeon.smoothprog', '1'), world.prop_history)

    def test_missing_control_stops(self):
        world = World([5.0, 6.0], control=False)
        self.run_world(world)
        self.assertEqual(world.percents, [])
        self.assertNotIn('aeon.smoothprog', world.props)

    def test_window_closing_stops(self):
        world = World([1.0 + n / 60.0 for n in range(60)], stop_after=2, rate='60')
        self.run_world(world)
        # the window is looked at every 0.25 s: updates go on until the next look finds it closed (15 or 16 at 60 a second)
        self.assertIn(len(world.percents), (15, 16))
        self.assertNotIn('aeon.smoothprog', world.props)


if __name__ == '__main__':
    unittest.main()
