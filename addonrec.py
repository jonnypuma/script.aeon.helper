# -*- coding: utf-8 -*-
"""Skin settings > System > Recommended add-ons (0.3.114, skin 0.56.53): RunScript(script.aeon.helper,addonrec) lists
the optional add-ons (resources/lib/recommended.py) with what each adds and whether it is installed. OK on one that is
missing installs it (Kodi's own Install dialog, dependencies included); when it lives in a repository that is not
installed yet, that repository is installed first from its zip (after a yes). The list opens again afterwards."""
import io
import json
import zipfile

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib import recommended

SKIN = 'skin.aeon.fuse'


def _items():
    """the list for this device: the Waveform Visualizer build that fits it (recommended.waveform_id)"""
    import platform
    return recommended.listed(platform.machine(), platform.system(), xbmc.getCondVisibility('System.Platform.Android'))


def _s(sid):
    return xbmcaddon.Addon(SKIN).getLocalizedString(sid)


def _has(aid):
    return xbmc.getCondVisibility('System.HasAddon(%s)' % aid)


def _version(aid):
    try:
        return xbmcaddon.Addon(aid).getAddonInfo('version')
    except Exception:
        return ''


def _icon(aid, installed):
    shot = 'special://skin/media/aeon/wizard/shots/addon_%s.jpg' % aid
    if xbmcvfs.exists(shot):
        return shot
    if installed:
        try:
            icon = xbmcaddon.Addon(aid).getAddonInfo('icon')
        except Exception:
            icon = ''
        for p in (icon, 'special://home/addons/%s/icon.png' % aid, 'special://home/addons/%s/resources/icon.png' % aid):
            if p and xbmcvfs.exists(p):
                return p
    return 'DefaultAddon.png'


def _rpc(method, params):
    return json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})))


def _wait(cond, seconds):
    mon = xbmc.Monitor()
    for _ in range(int(seconds * 4)):
        if cond() or mon.waitForAbort(0.25):
            return cond()
    return cond()


def install_repo(repo):
    """download the repository's zip, unpack it into the add-ons folder, enable it and read its add-on list"""
    name, url = recommended.REPOS[repo]
    try:
        from urllib.request import urlopen
        data = urlopen(url, timeout=30).read()
        zf = zipfile.ZipFile(io.BytesIO(data))
        if not recommended.zip_ok(zf.namelist(), repo):
            raise ValueError('unexpected zip')
        zf.extractall(xbmcvfs.translatePath('special://home/addons/'))
    except Exception as e:
        xbmc.log('[script.aeon.helper] addonrec: %s: %s' % (repo, e), xbmc.LOGWARNING)
        xbmcgui.Dialog().notification(name, _s(32790), xbmcgui.NOTIFICATION_ERROR)
        return False
    xbmc.executebuiltin('UpdateLocalAddons')
    xbmc.sleep(1500)
    _rpc('Addons.SetAddonEnabled', {'addonid': repo, 'enabled': True})
    if not _wait(lambda: _has(repo), 10):
        return False
    xbmc.executebuiltin('UpdateAddonRepos')
    # the repository's list has to come in before Kodi can find an add-on in it
    xbmc.sleep(6000)
    return True


def install(aid, name, need, ask=True):
    """ask=False (the wizard, the user ticked it): no repository question, Kodi's own install question answered Yes"""
    if need:
        rname = recommended.REPOS[need][0]
        if ask and not xbmcgui.Dialog().yesno(name, _s(32766) % (name, rname)):
            return
        if not install_repo(need):
            return
    xbmc.executebuiltin('InstallAddon(%s)' % aid)
    # Kodi asks first; then the download runs in the background
    asked = _wait(lambda: xbmc.getCondVisibility('Window.IsActive(yesnodialog)'), 5)
    if asked and not ask:
        xbmc.executebuiltin('SendClick(10100,11)')
    _wait(lambda: not xbmc.getCondVisibility('Window.IsActive(yesnodialog)'), 120)
    _wait(lambda: _has(aid), 90)


def show():
    pos = 0
    while True:
        rows = recommended.rows(_has, _version, _items())
        items = []
        for aid, name, sid, inst, ver, need in rows:
            state = (_s(32764) + (' ' + ver if ver else '')) if inst else _s(32765)
            li = xbmcgui.ListItem(name, '%s  ·  %s' % (state, _s(sid)))
            li.setArt({'icon': _icon(aid, inst), 'thumb': _icon(aid, inst)})
            items.append(li)
        done, total = recommended.count(_has, _items())
        heading = '%s  (%d / %d)' % (_s(32762), done, total)
        got = xbmcgui.Dialog().select(heading, items, useDetails=True, preselect=pos)
        xbmc.executebuiltin('Skin.SetString(aeon.rec.count,%d / %d)' % (done, total))
        if got < 0:
            return
        pos = got
        aid, name, _sid, inst, _ver, need = rows[got]
        if inst:
            xbmcgui.Dialog().notification(name, _s(32764), _icon(aid, True), 2500)
            continue
        install(aid, name, need)


def count():
    done, total = recommended.count(_has, _items())
    xbmc.executebuiltin('Skin.SetString(aeon.rec.count,%d / %d)' % (done, total))


def batch():
    """Setup wizard, add-ons step, Next: install every ticked add-on (Skin.HasSetting(aeon.wiz.add.<id>)) one after
    the other while the wizard goes on; the ticks are cleared."""
    todo = []
    for aid, name, _sid, inst, _ver, need in recommended.rows(_has, items=_items()):
        flag = 'aeon.wiz.add.%s' % aid
        if xbmc.getCondVisibility('Skin.HasSetting(%s)' % flag):
            xbmc.executebuiltin('Skin.Reset(%s)' % flag)
            if not inst:
                todo.append((aid, name))
    done = 0
    for aid, name in todo:
        need = dict((r[0], r[5]) for r in recommended.rows(_has, items=_items()))[aid]
        install(aid, name, need, ask=False)
        done += 1 if _has(aid) else 0
    if todo:
        xbmcgui.Dialog().notification(_s(32762), _s(32794) % ('%d / %d' % (done, len(todo))), 'DefaultAddon.png', 5000)
    count()
