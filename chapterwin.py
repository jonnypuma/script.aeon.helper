"""Chapter and bookmark pictures from the Trickplay sprites next to the playing video (service.trickplay / Jellyfin
layout, see resources/lib/chapthumbs.py), for the chapters dialog (VideoOSDBookmarks.xml).

Kodi gives every chapter a picture it extracts from the video on demand (image://video@...?chapter=N); on large HEVC
files that often never arrives and the dialog shows empty boxes. The skin draws the Trickplay crop under Kodi's own
picture, so it shows wherever Kodi has none.

A list item works out its picture's path once, when it is first drawn, so the crops and the path prefix
(Window(Home).Property(aeon.chap.prefix) = special://temp/aeonchap/<file token>_) must exist before the dialog opens:
- the service (ChapterPictures.tick) crops every chapter as soon as a video with chapters plays: <prefix>c<N>.jpg,
  the start of chapter N taken from Player.Chapters (start / end percentages);
- the dialog (RunScript(script.aeon.helper,chapthumbs)) crops its bookmarks: <prefix>b<resumepoint>.jpg, shown from
  the next time the dialog opens (a new bookmark has Kodi's own picture anyway).
Pillow comes with Kodi on Windows and CoreELEC; else the copy service.trickplay installs is used."""
import hashlib
import os
import sys
import threading
import time

import xbmc
import xbmcgui
import xbmcvfs

from resources.lib import chapthumbs

PROP = 'aeon.chap.prefix'
OUT = 'special://temp/aeonchap/'
TRICKPLAY_PIL = 'special://profile/addon_data/service.trickplay/system/python/site-packages'


def log(text):
    xbmc.log('[script.aeon.helper] chapters: %s' % text, xbmc.LOGINFO)


def pil_image():
    try:
        from PIL import Image
        return Image
    except ImportError:
        pass
    path = xbmcvfs.translatePath(TRICKPLAY_PIL)
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)
    try:
        from PIL import Image
        return Image
    except ImportError:
        return None


def token_for(playing):
    return hashlib.md5(playing.encode('utf-8')).hexdigest()[:12]


def prefix_for(playing):
    return OUT + token_for(playing) + '_'


def locate(playing):
    """(folder, sheet names, cols, rows, interval ms) of the video's Trickplay sprites, else None."""
    root = chapthumbs.sidecar_root(playing)
    if not root or not xbmcvfs.exists(root + '/'):
        return None
    dirs, _files = xbmcvfs.listdir(root + '/')
    pick = chapthumbs.choose_resolution(dirs)
    if not pick:
        return None
    name, (_width, cols, rows, interval) = pick
    folder = root + '/' + name + '/'
    sheets = chapthumbs.tile_order(xbmcvfs.listdir(folder)[1])
    if not sheets:
        return None
    return folder, sheets, cols, rows, interval


def crop(playing, points, abort=None):
    """Crop one picture per (seconds, name) in points into OUT as <token>_<name>.jpg (kept ones are not made again).
    Returns how many pictures exist afterwards."""
    found = locate(playing)
    if not found:
        return 0
    folder, sheets, cols, rows, interval = found
    image = pil_image()
    if image is None:
        log('Pillow is not available, no pictures')
        return 0
    token = token_for(playing)
    local = xbmcvfs.translatePath(OUT)
    if not os.path.isdir(local):
        os.makedirs(local)
    loaded = {}
    made = 0
    for seconds, name in points:
        if abort is not None and abort():
            break
        target = os.path.join(local, '%s_%s.jpg' % (token, name))
        if os.path.isfile(target):
            made += 1
            continue
        spot = chapthumbs.cell(seconds, interval, cols, rows, len(sheets))
        if spot is None:
            continue
        sheet, column, row = spot
        picture = loaded.get(sheet)
        if picture is None:
            copy = os.path.join(local, '%s_sheet%d.jpg' % (token, sheet))
            if not os.path.isfile(copy) and not xbmcvfs.copy(folder + sheets[sheet], copy):
                log('could not read %s' % sheets[sheet])
                continue
            try:
                picture = image.open(copy)
                picture.load()
            except (IOError, OSError) as error:
                log('could not open %s: %s' % (sheets[sheet], error))
                continue
            loaded[sheet] = picture
        width, height = picture.size[0] // cols, picture.size[1] // rows
        box = (column * width, row * height, column * width + width, row * height + height)
        picture.crop(box).convert('RGB').save(target, 'JPEG', quality=88)
        made += 1
    return made


def clean_others(playing):
    """Remove the pictures and sprite copies of other videos."""
    local = xbmcvfs.translatePath(OUT)
    token = token_for(playing)
    try:
        names = os.listdir(local)
    except OSError:
        return
    for name in names:
        if not name.startswith(token):
            try:
                os.remove(os.path.join(local, name))
            except OSError:
                pass


class ChapterPictures(object):
    """From the service loop: crop the chapter pictures of the video playing, once per video, in a thread."""
    WAIT = 20          # seconds to wait for Player.Chapters after a video starts

    def __init__(self):
        self.file = None
        self.since = 0.0
        self.done = False
        self.thread = None

    def reset(self):
        if self.file:
            xbmcgui.Window(10000).clearProperty(PROP)
        self.file = None
        self.done = False

    def tick(self):
        if xbmc.getSkinDir() != 'skin.aeon.fuse' or not xbmc.getCondVisibility('Player.HasVideo'):
            self.reset()
            return
        try:
            player = xbmc.Player()
            playing = player.getPlayingFile()
        except RuntimeError:
            return
        if playing != self.file:
            self.reset()
            self.file = playing
            self.since = time.time()
        if self.done or (self.thread and self.thread.is_alive()):
            return
        label = xbmc.getInfoLabel('Player.Chapters')
        if not label:
            if time.time() - self.since > self.WAIT:
                self.done = True
            return
        try:
            count = int(xbmc.getInfoLabel('Player.ChapterCount') or 0)
            total = player.getTotalTime()
        except (ValueError, RuntimeError):
            return
        if total <= 0:
            return
        self.done = True
        starts = chapthumbs.chapter_starts(label, count, total)
        points = [(seconds, 'c%d' % (number + 1)) for number, seconds in enumerate(starts)]
        self.thread = threading.Thread(target=self.work, args=(playing, points), name='aeon-chapters')
        self.thread.start()

    def work(self, playing, points):
        if not chapthumbs.sidecar_root(playing):
            return
        clean_others(playing)
        made = crop(playing, points, abort=lambda: self.file != playing)
        if made and self.file == playing:
            xbmcgui.Window(10000).setProperty(PROP, prefix_for(playing))
            log('%d chapter pictures from Trickplay' % made)


def main():
    """The chapters dialog: crop its bookmarks (chapters are done by the service) for the next time it opens."""
    player = xbmc.Player()
    if not player.isPlayingVideo():
        return
    try:
        playing = player.getPlayingFile()
    except RuntimeError:
        return
    monitor = xbmc.Monitor()
    for _ in range(40):                       # the dialog fills its list after it opens
        if xbmc.getCondVisibility('Window.IsVisible(videobookmarks)') and xbmc.getInfoLabel('Container(11).NumItems'):
            break
        if monitor.waitForAbort(0.1):
            return
    points = []
    try:
        count = int(xbmc.getInfoLabel('Container(11).NumItems') or 0)
    except ValueError:
        count = 0
    for i in range(count):
        if xbmc.getInfoLabel('Container(11).ListItemAbsolute(%d).Property(chapter)' % i):
            continue
        key = chapthumbs.file_key(xbmc.getInfoLabel('Container(11).ListItemAbsolute(%d).Property(resumepoint)' % i))
        if key:
            points.append((float(key), 'b' + key))
    if points and crop(playing, points):
        home = xbmcgui.Window(10000)
        if not home.getProperty(PROP):
            home.setProperty(PROP, prefix_for(playing))


if __name__ == '__main__':
    main()
