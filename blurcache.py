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
ACTIVE = 'Skin.HasSetting(aeon.fglass) + [Window.IsActive(videos) | Window.IsActive(music) | Window.IsActive(1168)]'   # 1168: Planner (0.3.74)
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


def make(source, target, radius=blur.RADIUS, done=None):
    try:
        data = read(source)
        out = blur.make(data, radius) if data else b''
        if not out:
            _failed.add(source)
            return
        with open(target + '.tmp', 'wb') as handle:
            handle.write(out)
        os.replace(target + '.tmp', target)
        if done:
            done(source, target)
        elif current() == source:
            publish(source, target)
        prune(os.path.dirname(target))
    except Exception as error:                # a backdrop that cannot be read simply gets no blurred copy
        _failed.add(source)
        xbmc.log('[script.aeon.helper] blur: %s' % error, xbmc.LOGINFO)
    finally:
        _busy.discard(source)


def tick(state):
    """Called from the service loop: follow the backdrop while Fused Glass shows a library window."""
    fantick(state)
    if not xbmc.getCondVisibility(ACTIVE):
        return
    # 0.3.111 (skin 0.56.45): the library view's own Panel blur (View settings), else Skin settings'
    step = xbmcgui.Window(10000).getProperty('aeon.vo.pblur') or xbmc.getInfoLabel('Skin.String(aeon.x.pblur)')
    radius = blur.panel_radius(step)
    if radius is None:                  # Expert settings > Panel blur Off: no blurred copy under the panels
        if state.get('blur') != ('off',):
            state['blur'] = ('off',)
            publish('', '')
        return
    source = current()
    if (source, radius) == state.get('blur'):
        return
    state['blur'] = (source, radius)
    if not source or source in _failed:
        return
    target = os.path.join(folder(), blur.cache_name(source, radius))
    if os.path.isfile(target):
        publish(source, target)
    elif source not in _busy:
        _busy.add(source)
        threading.Thread(target=make, args=(source, target, radius)).start()


FAN_ACTIVE = 'Window.IsActive(videos) | Window.IsActive(music)'


def fan_step():
    """0.3.108 (skin 0.56.42): the library view's own Fanart blur (View settings, Window(Home).Property(aeon.vo.fblur):
    off / light / medium / strong), else Skin settings' (Skin.String(aeon.x.fblur), '' = off)"""
    view = xbmcgui.Window(10000).getProperty('aeon.vo.fblur')
    if view:
        return view                  # 0.3.111: off / m2 .. p2 / z
    return xbmc.getInfoLabel('Skin.String(aeon.x.fblur)')      # '' = 0, the default (0.3.111)


def _fan_publish(source, target):
    if xbmc.getInfoLabel('$VAR[Aeon_V_Fan]') == source:
        xbmcgui.Window(10000).setProperty('aeon.fanblur', target)


def fantick(state):
    """0.3.104 Expert settings > Fanart blur (skin 0.56.28): a blurred copy of the library views' fanart in
    Window(Home).Property(aeon.fanblur). The copy of the item before stays until the new one is ready, so the
    background goes from one blurred picture to the next; with Fanart blur Off the property is cleared."""
    radius = blur.fanart_radius(fan_step())
    if not radius:
        if state.get('fanblur'):
            state['fanblur'] = None
            xbmcgui.Window(10000).clearProperty('aeon.fanblur')
        return
    if not xbmc.getCondVisibility(FAN_ACTIVE):
        return
    source = xbmc.getInfoLabel('$VAR[Aeon_V_Fan]')
    if (source, radius) == state.get('fanblur'):
        return
    state['fanblur'] = (source, radius)
    if not source or source in _failed:
        return
    target = os.path.join(folder(), blur.cache_name(source, radius))
    if os.path.isfile(target):
        xbmcgui.Window(10000).setProperty('aeon.fanblur', target)
    elif source not in _busy:
        _busy.add(source)
        threading.Thread(target=make, args=(source, target, radius, _fan_publish)).start()


FROST = 'Skin.HasSetting(aeon.fglass) + String.IsEqual(Skin.String(aeon.fgmenu),frost)'
AGBLUR = 'Skin.HasSetting(aeon.vglass) + !Skin.HasSetting(aeon.fglass)'   # 0.3.110: Aeon Glass, Panel blur (aeon.agblur)


def _unquote(path):
    """JSON-RPC art comes as image://<quoted path>/: the file behind it"""
    if path.startswith('image://'):
        from urllib.parse import unquote
        path = unquote(path[len('image://'):].rstrip('/'))
    return path


def _frost_make(raw, source, target, radius=blur.RADIUS):
    make(source, target, radius, done=lambda *_: None)
    home = xbmcgui.Window(10000)
    if os.path.isfile(target) and home.getProperty('aeon.bgfan') == raw:
        home.setProperty('aeon.bgfan.blur', target)
        home.setProperty('aeon.bgfan.blursrc', raw)


def frost(state):
    """0.3.93, Menu theme Frost (skin 0.56.12): a blurred copy of the settings backdrop. Window(Home).Property(
    aeon.bgfan.blur) = the copy, aeon.bgfan.blursrc = the aeon.bgfan it was made from (the skin shows the copy only
    while they match, so a stale copy never shows). 0.3.110 (skin 0.56.44): also Aeon Glass with Panel blur
    (Skin.String(aeon.agblur) light / medium / strong), at that step's radius."""
    radius = blur.menu_radius(xbmc.getCondVisibility(FROST),
                              xbmc.getInfoLabel('Skin.String(aeon.agblur)') if xbmc.getCondVisibility(AGBLUR) else '')
    if not radius:
        state.pop('frostsrc', None)
        return
    raw = xbmcgui.Window(10000).getProperty('aeon.bgfan')
    if not raw or (raw, radius) == state.get('frostsrc'):
        return
    state['frostsrc'] = (raw, radius)
    source = _unquote(raw)
    if source in _failed:
        return
    target = os.path.join(folder(), blur.cache_name(source, radius))
    if os.path.isfile(target):
        home = xbmcgui.Window(10000)
        home.setProperty('aeon.bgfan.blur', target)
        home.setProperty('aeon.bgfan.blursrc', raw)
    elif source not in _busy:
        _busy.add(source)
        threading.Thread(target=_frost_make, args=(raw, source, target, radius)).start()
