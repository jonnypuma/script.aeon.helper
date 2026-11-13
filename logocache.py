# -*- coding: utf-8 -*-
"""Trimmed clearlogos for the skin's Low list (addon_data/script.aeon.helper/logos).

The skin shows Window(Home).Property(aeon.logo) while aeon.logo.src is the logo of the item on screen; until the
trimmed copy exists it shows the original."""
import os
import threading

import xbmc
import xbmcgui
import xbmcvfs

from resources.lib import logotrim

FOLDER = 'special://profile/addon_data/script.aeon.helper/logos/'
VIEWS = 'Control.IsVisible(527)'            # views that line the logo up
_busy = set()
_failed = set()


def folder():
    path = xbmcvfs.translatePath(FOLDER)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def current():
    return xbmc.getInfoLabel('ListItem.Art(tvshow.clearlogo)') or xbmc.getInfoLabel('ListItem.Art(clearlogo)')


def publish(source, target):
    home = xbmcgui.Window(10000)
    home.setProperty('aeon.logo', target)
    home.setProperty('aeon.logo.src', source)


def make(source, target):
    try:
        handle = xbmcvfs.File(source)
        try:
            data = bytes(handle.readBytes())
        finally:
            handle.close()
        trimmed = logotrim.trim(data) if data else b''
        if not trimmed:
            _failed.add(source)
            return
        with open(target + '.tmp', 'wb') as out:
            out.write(trimmed)
        os.replace(target + '.tmp', target)
        if current() == source:
            publish(source, target)
    except Exception as error:               # a logo that cannot be read is simply shown as it is
        _failed.add(source)
        xbmc.log('[script.aeon.helper] logo: %s' % error, xbmc.LOGINFO)
    finally:
        _busy.discard(source)


def tick(state):
    """Called from the service loop: follow the logo of the focused item while a view that needs it is open."""
    if not xbmc.getCondVisibility(VIEWS):
        return
    source = current()
    if source == state.get('logo'):
        return
    state['logo'] = source
    if not source or source in _failed:
        return
    target = os.path.join(folder(), logotrim.cache_name(source))
    if os.path.isfile(target):
        publish(source, target)
    elif source not in _busy:
        _busy.add(source)
        threading.Thread(target=make, args=(source, target)).start()
