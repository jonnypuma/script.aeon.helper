# -*- coding: utf-8 -*-
"""Add-on art the skin cannot get from Kodi itself (skin 0.56.9; the user: "kodi addons, repos don't show fanart or
screenshots", "inside addon settings we are missing the addon fanart too").

Add-on browser (window 10040): Kodi gives a list item the add-on's icon and fanart, but its screenshots only to the
add-on information dialog. For the add-on in focus the service publishes
    aeon.ab.path            the item's path (the skin shows the shots only while it matches the item in focus)
    aeon.ab.shot1 .. 20     its screenshots (0.3.93: up to 20, the skin scrolls them)
    aeon.ab.shots           how many it has
from its addon.xml when it is installed, else from Kodi's add-on database (the version of the repository being
browsed: addons://repository.x/...).
Add-on settings (window 10140): Kodi puts the add-on's name in the hidden heading (label 2); the service finds the
add-on by that name and publishes aeon.as.fanart. Both are cleared when their window closes."""
import glob
import json
import os
import sqlite3
import threading
import xml.etree.ElementTree as ET
from urllib.parse import unquote

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import blurcache
from resources.lib import blur

SHOTS = 20             # 0.3.93: every screenshot an add-on names (up to 20), the skin scrolls them


def unquote_image(path):
    """the file behind Kodi's image://<quoted path>/ (JSON-RPC gives art that way)"""
    if path.startswith('image://'):
        path = unquote(path[len('image://'):].rstrip('/'))
    return path
BROWSER = 10040
SETTINGS = 10140


def rpc(method, params):
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return json.loads(xbmc.executeJSONRPC(request)).get('result') or {}


def split_path(path):
    """('repository.x' or '', 'plugin.video.y') from an add-on browser path; '' when it names no add-on"""
    p = (path or '').rstrip('/')
    if not p.startswith('addons://'):
        return '', ''
    parts = p[len('addons://'):].split('/')
    repo = parts[0] if parts and parts[0].startswith('repository.') else ''
    last = parts[-1] if len(parts) > 1 else ''
    return repo, last


def installed_shots(addon_id):
    try:
        folder = xbmcaddon.Addon(addon_id).getAddonInfo('path')
    except Exception:
        return None                                   # not installed (or not enabled): ask the database
    try:
        root = ET.parse(os.path.join(xbmcvfs.translatePath(folder), 'addon.xml')).getroot()
    except Exception:
        return []
    shots = []
    for node in root.iter('screenshot'):
        if node.text and node.text.strip():
            shots.append(os.path.join(folder, node.text.strip()))
    return shots


def database():
    found = sorted(glob.glob(os.path.join(xbmcvfs.translatePath('special://profile/Database/'), 'Addons*.db')))
    return found[-1] if found else ''


def version_key(text):
    return [int(p) if p.isdigit() else p for p in (text or '').replace('-', '.').split('.')]


def repo_shots(addon_id, repo):
    """the screenshots Kodi keeps for addon_id from the repository repo (any repository when repo is '')"""
    path = database()
    if not path:
        return []
    con = sqlite3.connect('file:%s?mode=ro' % path, uri=True, timeout=2)
    try:
        if repo:
            rows = con.execute('SELECT a.version, a.metadata FROM addons a JOIN addonlinkrepo l ON l.idAddon = a.id '
                               'JOIN repo r ON r.id = l.idRepo WHERE a.addonID = ? AND r.addonID = ?', (addon_id, repo)).fetchall()
        else:
            rows = []
        if not rows:
            rows = con.execute('SELECT version, metadata FROM addons WHERE addonID = ?', (addon_id,)).fetchall()
    finally:
        con.close()
    best = []
    for version, meta in sorted(rows, key=lambda r: version_key(r[0]), reverse=True):
        try:
            shots = json.loads(meta).get('screenshots') or []
        except Exception:
            shots = []
        if shots:
            best = shots
            break
    return best


class AddonArt(object):
    def __init__(self):
        self.path = None
        self.cache = {}
        self.names = None
        self.heading = None

    def set(self, values):
        home = xbmcgui.Window(10000)
        for name, value in values.items():
            if home.getProperty(name) != value:
                home.setProperty(name, value)

    def repo_fanart(self):
        """0.3.115: the fanart of the repository being browsed (addons://repository.x/...): the skin shows it where the
        item in focus has none (a folder such as Video add-ons), before its own backdrop (user, 2026-11-19)"""
        repo, _ = split_path(xbmc.getInfoLabel('Container.FolderPath'))
        art = ''
        if repo:
            key = ('fanart', repo)
            if key not in self.cache:
                details = rpc('Addons.GetAddonDetails', {'addonid': repo, 'properties': ['fanart']}).get('addon') or {}
                self.cache[key] = details.get('fanart') or ''
            art = self.cache[key]
        self.set({'aeon.ab.repofanart': art})

    def browser(self):
        path = xbmc.getInfoLabel('Container(50).ListItem.FileNameAndPath')
        if path == self.path:
            return
        self.path = path
        self.repo_fanart()
        repo, addon_id = split_path(path)
        shots = []
        if addon_id and '.' in addon_id:
            key = (repo, addon_id)
            if key not in self.cache:
                found = installed_shots(addon_id)
                if not found:                        # not installed, or its addon.xml names none: the repository's
                    found = repo_shots(addon_id, repo)
                self.cache[key] = found or []
            shots = self.cache[key]
        values = {'aeon.ab.path': path if shots else '', 'aeon.ab.shots': str(len(shots)) if shots else ''}
        for k in range(1, SHOTS + 1):
            values['aeon.ab.shot%d' % k] = shots[k - 1] if k <= len(shots) else ''
        self.set(values)

    def settings(self):
        heading = xbmc.getInfoLabel('Control.GetLabel(2)')
        if heading == self.heading:
            return
        self.heading = heading
        name = heading
        word = xbmc.getLocalizedString(10004)                  # "Settings - <add-on>"
        for sep in (' - ', ' – ', ': '):
            if word and heading.startswith(word + sep):
                name = heading[len(word + sep):]
                break
        fanart = ''
        for attempt in (0, 1):
            if self.names is None or attempt:
                found = rpc('Addons.GetAddons', {'properties': ['name', 'fanart'], 'installed': True}).get('addons') or []
                self.names = dict((a.get('name'), a.get('fanart') or '') for a in found)
            if name in self.names:
                fanart = self.names[name]
                break
        # 0.3.91: a blurred copy (the helper's blur cache), so the settings panels read as on top of it (the user, on
        # Skippy's fanart with its light card: "is this panel on top??? looks like it's behind something")
        self.set({'aeon.as.fanart': ''})
        source = unquote_image(fanart)
        if not source:
            return
        target = os.path.join(blurcache.folder(), blur.cache_name(source))
        if os.path.isfile(target):
            self.set({'aeon.as.fanart': target})
        else:
            threading.Thread(target=self.blur_later, args=(heading, source, target)).start()

    def blur_later(self, heading, source, target):
        blurcache.make(source, target)
        if os.path.isfile(target) and self.heading == heading:
            self.set({'aeon.as.fanart': target})

    def tick(self):
        try:
            dialog = xbmcgui.getCurrentWindowDialogId()
            if dialog == SETTINGS:
                self.settings()
            elif self.heading is not None:
                self.heading = None
                self.set({'aeon.as.fanart': ''})
            window = xbmcgui.getCurrentWindowId()
            if window == BROWSER and dialog == 9999:          # no dialog: Container(50) is the browser's list
                self.browser()
            elif window == BROWSER:
                pass                                          # a dialog over it (information, settings): keep
            elif self.path is not None:
                self.path = None
                self.set(dict([('aeon.ab.path', ''), ('aeon.ab.shots', ''), ('aeon.ab.repofanart', '')] + [('aeon.ab.shot%d' % k, '') for k in range(1, SHOTS + 1)]))
        except Exception as error:                   # never stop the service over this
            xbmc.log('[script.aeon.helper] add-on art: %s' % error, xbmc.LOGINFO)
