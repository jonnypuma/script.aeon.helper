"""Smooth song progress (Skin settings > Motion, memory, reset; skin 0.52.1, on by default since 0.52.3): in the Fused
Glass Now playing card the song's progress glides instead of stepping.

Kodi's progress control reads its <info> as a whole percent (CGUIProgressControl::UpdateInfo uses GetInt), so the
card's fill (820 px) jumps 8 px at every 1 % of the song: every 2.4 s on a four-minute song. Python's
ControlProgress.setPercent takes a float. While the Now playing window (visualisation, 12006) is up and the setting is
on (!Skin.HasSetting(aeon.smoothprogress.off)), a short-lived thread sets the card's second progress control (id 4801,
no <info>, Includes_Aeon_Music.xml) from the player's own time.

How often (Skin settings > Updates per second, Skin.String(aeon.smoothprogress.rate)): '' = Screen, as often as Kodi
draws the GUI (System.FPS, read again every quarter second; the screen mode's refresh rate when Kodi gives no
number), or 10, 25, 30, 60. Updates keep to a steady clock (each one is due 1 / rate after the one before), so the
time the Python calls take does not slow the rate down. While paused: four a second.

Measured on the CoreELEC box (Kodi 22, 2026-11-15): xbmc.Player().getTime() moves in 10 ms steps and stays within
7 ms of a steady clock, and a read costs about 1 microsecond. So it is read for every update instead of being
interpolated between rare reads: pause, seek, buffering and the next song need no handling of their own (only the
small wobble while paused, see follow).

The visualisation window keeps its controls while it is closed (KEEP_IN_MEMORY), but a skin reload builds them again,
so the control is looked up for every update instead of being kept. Window(Home).Property(aeon.smoothprog) = 1 tells
the skin to show this control instead of the stock one (Player.Progress); it is set after the first update and
cleared when the thread ends, so the card never shows an unset fill."""
import re
import threading
import time

import xbmc
import xbmcgui

WINDOW = 12006            # visualisation: MusicVisualisation.xml
CONTROL = 4801            # Includes_Aeon_Music.xml: the card's progress without <info>
PROP = 'aeon.smoothprog'
RATES = {'10': 10.0, '25': 25.0, '30': 30.0, '60': 60.0}
LOWEST, HIGHEST = 10.0, 120.0   # bounds for Screen
FALLBACK = 60.0
SLOWEST = 0.25            # how often the thread looks at the window, the setting and pause; the wait while paused
ACTIVE = ('!Skin.HasSetting(aeon.smoothprogress.off) + Skin.HasSetting(aeon.fglass) + Player.HasAudio'
          ' + Window.IsVisible(visualisation) + !System.ScreenSaverActive')


def log(text):
    xbmc.log('[script.aeon.helper] smooth progress: %s' % text, xbmc.LOGINFO)


def screen_rate():
    """Frames Kodi draws a second (System.FPS), else the screen mode's refresh rate, else 60; within 10-120."""
    try:
        fps = float(xbmc.getInfoLabel('System.FPS'))
    except ValueError:
        fps = 0.0
    if fps < LOWEST:
        match = re.search(r'@\s*([\d.]+)', xbmc.getInfoLabel('System.ScreenMode'))
        fps = float(match.group(1)) if match else FALLBACK
    return min(HIGHEST, max(LOWEST, fps))


def wanted_rate():
    return RATES.get(xbmc.getInfoLabel('Skin.String(aeon.smoothprogress.rate)')) or screen_rate()


class SmoothProgress(object):
    """service.py calls tick() every 0.3 s; the thread runs only while ACTIVE holds."""

    def __init__(self):
        self.thread = None

    def tick(self):
        if self.thread is not None and self.thread.is_alive():
            return
        if xbmc.getSkinDir() == 'skin.aeon.fuse' and xbmc.getCondVisibility(ACTIVE):
            self.thread = threading.Thread(target=self.follow, name='aeon-smoothprog')
            self.thread.start()

    def follow(self):
        monitor = xbmc.Monitor()
        player = xbmc.Player()
        window = xbmcgui.Window(WINDOW)
        home = xbmcgui.Window(10000)
        started = time.monotonic()
        updates = 0
        shown = False
        paused = False
        rate = FALLBACK
        next_check = 0.0
        due = started                                 # when the next update is due
        last = (0.0, 0.0)                             # (length, position) of the last update
        try:
            while True:
                now = time.monotonic()
                if now >= next_check:
                    if not xbmc.getCondVisibility(ACTIVE):
                        break
                    paused = xbmc.getCondVisibility('Player.Paused')
                    rate = wanted_rate()
                    next_check = now + SLOWEST
                try:
                    total = player.getTotalTime()
                    position = player.getTime()
                except RuntimeError:                  # playback ended between two looks
                    break
                if total <= 0:                        # a stream without a length: the stock fill (empty) is right
                    if shown:
                        home.clearProperty(PROP)
                        shown = False
                    period = SLOWEST
                else:
                    # while paused Kodi's time wobbles by a few milliseconds (the audio output's delay estimate): never
                    # step back by less than half a second, so the edge pixel cannot flicker; a seek back or the next
                    # song still moves it at once
                    if total == last[0] and 0.0 < last[1] - position < 0.5:
                        position = last[1]
                    last = (total, position)
                    try:
                        window.getControl(CONTROL).setPercent(min(100.0, max(0.0, position * 100.0 / total)))
                    except Exception as error:        # no such control: an older skin, or the skin is reloading
                        log('stopped: %s' % error)
                        break
                    updates += 1
                    if not shown:
                        home.setProperty(PROP, '1')
                        shown = True
                    period = SLOWEST if paused else 1.0 / rate
                due += period
                now = time.monotonic()
                if due < now - period:                # fell behind (a busy moment): start counting again from now
                    due = now
                if monitor.waitForAbort(max(0.001, due - now)):
                    break
        finally:
            home.clearProperty(PROP)
            seconds = time.monotonic() - started
            log('%d updates in %.0f s (%.1f a second, last rate %.1f)'
                % (updates, seconds, updates / seconds if seconds else 0.0, rate))
