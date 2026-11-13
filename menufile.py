# -*- coding: utf-8 -*-
"""The Home menu files of script.skinvariables (userdata/addon_data/script.skinvariables/nodes/skin.aeon.fuse).

skinvariables keeps each file in a Home property until Kodi restarts, so after a change made here the files are put
there again and the lists are told to reload."""
import json
import os
import time
import uuid

import xbmc
import xbmcgui
import xbmcvfs

FOLDER = 'special://profile/addon_data/script.skinvariables/nodes/skin.aeon.fuse/'
MENU = 'skinvariables-shortcut-aeonmenu.json'
ANDROID = 'RunScript(script.aeon.helper,android)'


def folder():
    return xbmcvfs.translatePath(FOLDER)


def reload():
    home = xbmcgui.Window(10000)
    base = folder()
    if not os.path.isdir(base):
        return
    for name in os.listdir(base):
        if not name.endswith('.json'):
            continue
        with open(os.path.join(base, name), 'r') as handle:
            text = handle.read()
        json.loads(text)                     # never hand over a broken file
        home.setProperty('SkinVariables.ShortcutsNode.skin.aeon.fuse-%s' % name, text)
    home.setProperty('SkinVariables.ShortcutsNode.Reload', str(time.time()))


def add_power_item(menu, label, path, before='Powerdown()'):
    """Put an entry into the sub-menu of Power (the item whose sub-menu holds Powerdown()), before Shut down.
    Returns True when the list changed. No Kodi calls: testable."""
    for item in menu:
        entries = item.get('submenu') or []
        paths = [entry.get('path') for entry in entries]
        if before not in paths:
            continue
        if path in paths:
            return False
        entries.insert(paths.index(before), {'label': label, 'icon': '', 'path': path, 'target': '', 'guid': 'guid-%s' % uuid.uuid4().hex[:8]})
        return True
    return False


def ensure_android():
    """CoreELEC only, once: 'Reboot to Android' joins the Power row (it can be removed again in the menu editor)."""
    if 'coreelec' not in xbmc.getInfoLabel('System.OSVersionInfo').lower():
        return
    if xbmc.getInfoLabel('Skin.String(aeon.power.android)'):
        return
    path = os.path.join(folder(), MENU)
    try:
        with open(path, 'r') as handle:
            menu = json.load(handle)
    except (IOError, OSError, ValueError):
        return
    if add_power_item(menu, xbmc.getInfoLabel('$LOCALIZE[31371]') or 'Reboot to Android', ANDROID):
        with open(path, 'w') as handle:
            json.dump(menu, handle, indent=4)
        reload()
    xbmc.executebuiltin('Skin.SetString(aeon.power.android,1)')
