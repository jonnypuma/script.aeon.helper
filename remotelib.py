# -*- coding: utf-8 -*-
"""Library update / clean for the skin (0.3.114, skin 0.56.53): RunScript(script.aeon.helper,lib,update|clean,video|music)
runs UpdateLibrary / CleanLibrary here, or - with Skin settings > Libraries > Update and clean on another Kodi on - sends
it to that Kodi's JSON-RPC (resources/lib/libremote.py) and says when an update there has finished.
RunScript(script.aeon.helper,libremote,address|user|password|test) are the settings rows. The address and user name are
skin strings (aeon.libremote.host / .user, shown on the rows); the password is this add-on's own setting
(libremote_pass, never shown, not in the skin's Export file)."""
import xbmc
import xbmcaddon
import xbmcgui

from resources.lib import libremote

SKIN = 'skin.aeon.fuse'
ICON = 'special://skin/media/common/aeon_ic_refresh.png'


def _s(sid):
    return xbmcaddon.Addon(SKIN).getLocalizedString(sid)


def _conf():
    return (xbmc.getInfoLabel('Skin.String(aeon.libremote.host)'), xbmc.getInfoLabel('Skin.String(aeon.libremote.user)'),
            xbmcaddon.Addon().getSetting('libremote_pass'))


def remote_on():
    return xbmc.getCondVisibility('Skin.HasSetting(aeon.libremote)')


def _fail(host, err):
    if err.kind == 'address':
        msg = _s(32780)
    elif err.kind == 'auth':
        msg = _s(32785)
    else:
        msg = err.detail or err.kind
    xbmc.log('[script.aeon.helper] libremote %s: %s' % (libremote.display(host), err), xbmc.LOGWARNING)
    xbmcgui.Dialog().notification(libremote.display(host) or _s(32771), msg, xbmcgui.NOTIFICATION_ERROR, 6000)


def run(action, kind):
    if action not in ('update', 'clean') or kind not in libremote.KINDS:
        return
    if not remote_on():
        xbmc.executebuiltin('%s(%s)' % ('UpdateLibrary' if action == 'update' else 'CleanLibrary', kind))
        return
    host, user, pwd = _conf()
    try:
        ok = libremote.library(host, user, pwd, action, kind)
    except libremote.RemoteError as e:
        _fail(host, e)
        return
    name = libremote.display(host)
    xbmcgui.Dialog().notification(name, _s(32781 if action == 'update' else 32782) if ok else _s(32789), ICON, 4000)
    if ok and action == 'update':
        follow(host, user, pwd, kind)


def follow(host, user, pwd, kind):
    """wait for the scan there to start and end (5 s steps, at most 3 hours), then say so and refresh the lists here"""
    mon = xbmc.Monitor()
    seen = False
    for step in range(3 * 60 * 12):
        if mon.waitForAbort(5):
            return
        try:
            busy = libremote.scanning(host, user, pwd, kind)
        except libremote.RemoteError:
            return
        if busy:
            seen = True
        elif seen or step >= 2:
            break
    xbmcgui.Dialog().notification(libremote.display(host), _s(32786), ICON, 5000)
    xbmc.executebuiltin('Container.Refresh')


def setting(what):
    if what == 'address':
        now = xbmc.getInfoLabel('Skin.String(aeon.libremote.host)')
        got = xbmcgui.Dialog().input(_s(32772), now or 'http://')
        if got is not None and got != now:
            got = got.strip()
            if got in ('http://', 'https://'):
                got = ''
            xbmc.executebuiltin('Skin.SetString(aeon.libremote.host,%s)' % got if got else 'Skin.Reset(aeon.libremote.host)')
            xbmc.executebuiltin('Skin.Reset(aeon.libremote.status)')
    elif what == 'user':
        now = xbmc.getInfoLabel('Skin.String(aeon.libremote.user)')
        got = xbmcgui.Dialog().input(_s(32773), now)
        if got is not None and got != now:
            xbmc.executebuiltin('Skin.SetString(aeon.libremote.user,%s)' % got if got else 'Skin.Reset(aeon.libremote.user)')
            xbmc.executebuiltin('Skin.Reset(aeon.libremote.status)')
    elif what == 'password':
        got = xbmcgui.Dialog().input(_s(32774), option=xbmcgui.ALPHANUM_HIDE_INPUT)
        if got is None:
            return
        xbmcaddon.Addon().setSetting('libremote_pass', got)
        xbmc.executebuiltin('Skin.SetBool(aeon.libremote.pwset)' if got else 'Skin.Reset(aeon.libremote.pwset)')
        xbmc.executebuiltin('Skin.Reset(aeon.libremote.status)')
    elif what == 'test':
        test()


def test():
    host, user, pwd = _conf()
    xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    try:
        ver = libremote.version(host, user, pwd)
    except libremote.RemoteError as e:
        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
        msg = _s(32780) if e.kind == 'address' else (_s(32785) if e.kind == 'auth' else (e.detail or e.kind))
        xbmc.executebuiltin('Skin.SetString(aeon.libremote.status,%s)' % _s(32789))
        xbmcgui.Dialog().ok(_s(32775), _s(32783) % (libremote.display(host) or '-', msg))
        return
    xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
    xbmc.executebuiltin('Skin.SetString(aeon.libremote.status,%s)' % ver)
    xbmcgui.Dialog().ok(_s(32775), _s(32784) % (libremote.display(host), ver))
