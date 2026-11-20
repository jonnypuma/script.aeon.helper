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
MENU2 = 'skinvariables-shortcut-aeonmenu2.json'     # Movie sets and the custom items: their widgets and submenus
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


def add_custom_nodes(menu, count=10):
    """The custom items' entries in the aeonmenu2 file (guid-aeon0012 = custom item 1 ... guid-aeon0021 = 10): the ones
    a file from before skin 0.54.0 lacks (it had three) are added, empty. Returns True when the list changed.
    No Kodi calls: testable."""
    have = set(item.get('guid') for item in menu)
    changed = False
    for k in range(1, count + 1):
        guid = 'guid-aeon%04d' % (11 + k)
        if guid not in have:
            menu.append({'label': 'Custom item %d' % k, 'icon': '', 'path': '', 'target': '', 'guid': guid,
                         'submenu': [], 'widgets': []})
            changed = True
    return changed


def clear_custom_node(menu, k):
    """Delete (0.3.115): custom item k's entry in the aeonmenu2 file back to empty (no widgets, no submenu).
    Returns True when it changed. No Kodi calls: testable."""
    guid = 'guid-aeon%04d' % (11 + k)
    for item in menu:
        if item.get('guid') == guid:
            empty = {'label': 'Custom item %d' % k, 'icon': '', 'path': '', 'target': '', 'submenu': [], 'widgets': []}
            if any(item.get(key) != value for key, value in empty.items()):
                item.update(empty)
                return True
    return False


def clear_custom(k):
    path = os.path.join(folder(), MENU2)
    try:
        with open(path, 'r') as handle:
            menu = json.load(handle)
    except (IOError, OSError, ValueError):
        return
    if clear_custom_node(menu, k):
        with open(path, 'w') as handle:
            json.dump(menu, handle, indent=4)
        reload()


def ensure_custom_nodes():
    """Skin 0.54.0 has ten custom items: the user's aeonmenu2 file gets the entries of items 4-10, so their widgets
    and submenus can be edited (the skin's own copy has them; a saved file from before has three)."""
    path = os.path.join(folder(), MENU2)
    try:
        with open(path, 'r') as handle:
            menu = json.load(handle)
    except (IOError, OSError, ValueError):
        return                               # no saved file: skinvariables reads the skin's own, which has them
    if add_custom_nodes(menu):
        with open(path, 'w') as handle:
            json.dump(menu, handle, indent=4)
        reload()
