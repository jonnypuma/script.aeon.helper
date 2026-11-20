# -*- coding: utf-8 -*-
"""Skin settings > System > Export / Import skin settings (skin 0.56.42).
Export: every skin setting as Kodi has it now (JSON-RPC Settings.GetSkinSettings) with Kodi's theme, colours and font
setting, to aeon-fuse-settings-<date>-<time>.json in a folder the user picks (any Kodi source, smb:// too).
Import: a file picked, a yes / no with its date, then only the settings that differ are set (Settings.SetSkinSettingValue,
the Skin builtin when Kodi refuses one), Font.xml written again when a font choice changed, Kodi's theme last, and Kodi
restarted (Linux; elsewhere the skin reloads, as after the setup wizard). File format and plan: resources/lib/backup.py."""
import json
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib import backup

SKIN = 'skin.aeon.fuse'
ICON = 'special://home/addons/%s/resources/icon.png' % SKIN


def text(ident, fallback):
    label = '$ADDON[%s %d]' % (SKIN, ident) if ident >= 32000 else '$LOCALIZE[%d]' % ident
    return xbmc.getInfoLabel(label) or fallback


def rpc(method, params=None):
    request = {'jsonrpc': '2.0', 'id': 1, 'method': method}
    if params is not None:
        request['params'] = params
    return json.loads(xbmc.executeJSONRPC(json.dumps(request))).get('result')


def kodi_now():
    return dict((key, (rpc('Settings.GetSettingValue', {'setting': key}) or {}).get('value')) for key in backup.KODI)


def skin_now():
    return (rpc('Settings.GetSkinSettings') or {}).get('settings') or []


def export(folder=None):
    """folder: settings,export,<folder> skips the folder dialog (scripts, tests)"""
    heading = text(32725, 'Export skin settings')
    folder = folder or xbmcgui.Dialog().browse(3, text(32731, 'Folder for the settings file'), 'files')
    if not folder:
        return
    saved = time.strftime('%Y-%m-%d %H:%M')
    try:
        version = xbmcaddon.Addon(SKIN).getAddonInfo('version')
    except RuntimeError:
        version = ''
    data = backup.build(skin_now(), kodi_now(), version, saved)
    name = backup.file_name(saved)
    path = folder + name if folder.endswith(('/', '\\')) else folder + '/' + name
    handle = xbmcvfs.File(path, 'w')
    try:
        written = handle.write(bytearray(backup.dump(data).encode('utf-8')))
    finally:
        handle.close()
    if not written or not xbmcvfs.exists(path):
        xbmcgui.Dialog().ok(heading, text(32736, 'The file could not be written.'))
        return
    xbmcgui.Dialog().notification(heading, text(32733, 'Saved: %s').replace('%s', name), ICON, 5000)


def platform():
    return next((name for name in ('android', 'windows', 'osx', 'linux') if xbmc.getCondVisibility('System.Platform.%s' % name)), '')


def import_(path=None):
    """path: settings,import,<file> skips the file dialog (the yes / no still asks)"""
    from resources.lib import wizard
    heading = text(32726, 'Import skin settings')
    path = path or xbmcgui.Dialog().browse(1, text(32732, 'Settings file to load'), 'files', '.json')
    if not path:
        return
    handle = xbmcvfs.File(path)
    try:
        raw = handle.readBytes()
    finally:
        handle.close()
    data = backup.load(bytes(raw).decode('utf-8', 'replace'))
    if data is None:
        xbmcgui.Dialog().ok(heading, text(32735, 'This file does not hold Aeon Fuse settings.'))
        return
    restart = wizard.can_restart(platform())
    question = text(32734, 'Load the settings saved on %s? Your current skin settings are replaced.').replace('%s', data.get('saved') or '?')
    question += '[CR]' + (text(32737, 'Kodi restarts to apply them.') if restart else
                          text(32738, 'The skin reloads; restart Kodi afterwards so every setting is read again.'))
    if not xbmcgui.Dialog().yesno(heading, question):
        return
    now = backup.build(skin_now(), {}, '', '')['settings']
    changes = backup.plan(data, now)
    for key, value in changes:
        if rpc('Settings.SetSkinSettingValue', {'setting': key, 'value': value}) is not True:
            xbmc.executebuiltin(backup.builtin(key, value))
    kodi = backup.kodi_plan(data, kodi_now())
    if not changes and not kodi:
        xbmcgui.Dialog().notification(heading, text(32739, 'These settings are already in use.'), ICON, 4000)
        return
    xbmc.log('script.aeon.helper: settings import: %d skin settings, %d Kodi settings' % (len(changes), len(kodi)), xbmc.LOGINFO)
    monitor = xbmc.Monitor()
    if backup.fonts_changed(changes):
        import fontpick
        try:
            fontpick.apply()
        except Exception as error:
            xbmc.log('script.aeon.helper: settings import: fonts: %r' % (error,), xbmc.LOGWARNING)
    for key, value in kodi:
        monitor.waitForAbort(0.3)
        if rpc('Settings.SetSettingValue', {'setting': key, 'value': value}) is not True and key == 'lookandfeel.skincolors' \
                and isinstance(value, str) and not value.endswith('.xml'):
            rpc('Settings.SetSettingValue', {'setting': key, 'value': value + '.xml'})
    monitor.waitForAbort(1.0)
    if restart:
        xbmc.executebuiltin('RestartApp')
    elif not any(key == 'lookandfeel.skintheme' for key, _value in kodi):
        xbmc.executebuiltin('ReloadSkin()')


def main(what, path=None):
    if what == 'export':
        export(path)
    elif what == 'import':
        import_(path)
