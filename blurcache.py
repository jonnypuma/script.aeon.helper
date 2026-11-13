# -*- coding: utf-8 -*-
"""Blurred backdrops for the Fused Glass theme (addon_data/script.aeon.helper/blur).

While Fused Glass is on and a library window is open, the service follows the skin's backdrop ($VAR[FG_BlurSrc]) and
publishes Window(Home).Property(aeon.blur) = the blurred copy, aeon.blur.src = the backdrop it was made from. The
skin shows the copy only while aeon.blur.src is the backdrop on screen, so a stale copy never shows. Pictures come from
Kodi's texture cache when they are there (no download), else from their source. The folder keeps the newest copies."""
import os
import threading

import xbmc
import xbmcgui
import xbmcvfs

from resources.lib import blur

FOLDER = 'special://profile/addon_data/script.aeon.helper/blur/'
ACTIVE = 'Skin.HasSetting(aeon.fglass) + [Window.IsActive(videos) | Window.IsActive(music)]'
KEEP = 300
_busy = set()
_failed = set()


def folder():
    path = xbmcvfs.translatePath(FOLDER)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def current():
    return xbmc.getInfoLabel('$VAR[FG_BlurSrc]')


def publish(source, target):
    home = xbmcgui.Window(10000)
    home.setProperty('aeon.blur', target)
    home.setProperty('aeon.blur.src', source)


def cached_file(source):
    """Kodi's cached copy of a picture (special://thumbnails/<c>/<crc>.jpg|png), or None."""
    try:
        name = xbmc.getCacheThumbName(source)
    except Exception:
        return None
    base = os.path.splitext(name)[0]
    if not base:
        return None
    for ext in ('.jpg', '.png'):
        path = xbmcvfs.translatePath('special://thumbnails/%s/%s%s' % (base[0], base, ext))
        if os.path.isfile(path):
            return path
    return None


def read(source):
    local = cached_file(source)
    if local:
        with open(local, 'rb') as handle:
            return handle.read()
    handle = xbmcvfs.File(source)
    try:
        return bytes(handle.readBytes())
    finally:
        handle.close()


def prune(path):
    try:
        names = [os.path.join(path, n) for n in os.listdir(path) if n.endswith('.jpg')]
        if len(names) <= KEEP:
            return
        names.sort(key=os.path.getmtime)
        for name in names[:len(names) - KEEP]:
            os.remove(name)
    except OSError:
        pass


def make(source, target):
    try:
        data = read(source)
        out = blur.make(data) if data else b''
        if not out:
            _failed.add(source)
            return
        with open(target + '.tmp', 'wb') as handle:
            handle.write(out)
        os.replace(target + '.tmp', target)
        if current() == source:
            publish(source, target)
        prune(os.path.dirname(target))
    except Exception as error:                # a backdrop that cannot be read simply gets no blurred copy
        _failed.add(source)
        xbmc.log('[script.aeon.helper] blur: %s' % error, xbmc.LOGINFO)
    finally:
        _busy.discard(source)


def tick(state):
    """Called from the service loop: follow the backdrop while Fused Glass shows a library window."""
    if not xbmc.getCondVisibility(ACTIVE):
        return
    source = current()
    if source == state.get('blur'):
        return
    state['blur'] = source
    if not source or source in _failed:
        return
    target = os.path.join(folder(), blur.cache_name(source))
    if os.path.isfile(target):
        publish(source, target)
    elif source not in _busy:
        _busy.add(source)
        threading.Thread(target=make, args=(source, target)).start()
