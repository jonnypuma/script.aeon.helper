# -*- coding: utf-8 -*-
"""RunScript(script.aeon.helper,fonts): pick a font combination (heading + text font, fonts.PRESETS) or a font
family for each section of the Aeon Fuse skin.

The choices are skin strings (aeon.font.<section>, '' = follow the font set). On closing the list the skin's Font.xml
is rewritten (resources/lib/fonts.py) and the skin reloads. sync() does the same check without a dialog: the service
calls it at start-up, so a skin update that ships a fresh Font.xml gets the user's fonts back."""
import os
import xml.etree.ElementTree as ET

import xbmc
import xbmcgui
import xbmcvfs

from resources.lib import fonts

SKIN = 'skin.aeon.fuse'
# section -> (skin string id of its name, English fallback)
NAMES = (('home', 31019, 'Home'), ('library', 31991, 'Library'), ('headings', 31840, 'Headings'),
         ('settings', 31841, 'Settings pages'), ('player', 31842, 'Player'))


def text(ident, fallback):
    # the skin's strings from 32000 up are only reachable through $ADDON
    label = '$ADDON[%s %d]' % (SKIN, ident) if ident >= 32000 else '$LOCALIZE[%d]' % ident
    return xbmc.getInfoLabel(label) or fallback


def skin_dir():
    return xbmcvfs.translatePath('special://home/addons/%s/' % SKIN)


def font_xml():
    return os.path.join(skin_dir(), '1080i', 'Font.xml')


def read():
    with open(font_xml(), 'r', encoding='utf-8') as handle:
        return handle.read()


def exists(name):
    if '://' in name:
        return xbmcvfs.exists(name)
    return os.path.exists(os.path.join(skin_dir(), 'fonts', name)) or xbmcvfs.exists('special://xbmc/media/Fonts/' + name)


def installed(source):
    """Font sets whose files are all there, in file order."""
    found = [ident for ident, names in fonts.files(source).items() if all(exists(name) for name in names)]
    found += [name for name, _pattern in fonts.WEIGHTED if all(exists(path) for path in fonts.weighted_files(name))]
    return found + [name for name, path in fonts.EXTRA if exists(path)]


def offered(source, keep=(), section=''):
    """Families for the picker: installed and with a real bold face (bold text is used all over the skin).
    Headings also get the one-weight faces (a heading is drawn in one weight anyway).
    A family that is already chosen stays in the list."""
    sets = fonts.fontsets(source)
    return [name for name in installed(source)
            if fonts.has_bold(name, sets) or name in keep or (section == 'headings' and name in fonts.ONEFILE)]


def choices():
    return dict((key, xbmc.getInfoLabel('Skin.String(aeon.font.%s)' % key)) for key, _p in fonts.SECTIONS)


def apply(source=None):
    """Write Font.xml for the current choices. True when the file changed."""
    source = source if source is not None else read()
    wanted = fonts.clean(choices(), fonts.fontsets(source))
    # a family that was removed (font add-on uninstalled) falls back to the font set
    ok = installed(source)
    for key, value in list(wanted.items()):
        if value and value not in ok:
            wanted[key] = ''
    new = fonts.build(source, wanted)
    if new == source:                           # compared whole: a newer helper may write other fonts for the same choices
        return False
    ET.fromstring(new.encode('utf-8'))          # never write a file Kodi cannot read
    path = font_xml()
    with open(path + '.new', 'w', encoding='utf-8', newline='') as handle:
        handle.write(new)
    os.replace(path + '.new', path)
    return True


def sync():
    if xbmc.getSkinDir() != SKIN:
        return
    try:
        if apply():
            xbmc.executebuiltin('ReloadSkin()')
    except Exception as error:
        xbmc.log('script.aeon.helper: fonts: %r' % (error,), xbmc.LOGWARNING)


class Picker(xbmcgui.WindowXMLDialog):
    """script-aeon-fonts.xml (in the skin): the rows on the left, a mock-up in the focused row's fonts on the right.
    A row is (label, h, b): h = preview number of the family for the mock-up's title, b = the one for the rest
    (0 follows the font set, else the family's place among all families + 1)."""
    LIST = 100

    def setup(self, heading, section, rows, current):
        self.heading, self.section, self.rows, self.current = heading, section, rows, current
        self.picked = -1

    def onInit(self):
        self.setProperty('section', self.section)
        try:
            self.getControl(1).setLabel(self.heading)
        except RuntimeError:
            pass
        items = []
        for label, head, body in self.rows:
            item = xbmcgui.ListItem(label)
            item.setProperty('h', str(head))
            item.setProperty('b', str(body))
            items.append(item)
        box = self.getControl(self.LIST)
        box.reset()
        box.addItems(items)
        box.selectItem(self.current)
        items[self.current].select(True)
        self.setFocusId(self.LIST)

    def onClick(self, control):
        if control == self.LIST:
            self.picked = self.getControl(self.LIST).getSelectedPosition()
            self.close()


def choose(heading, section, rows, current):
    """Position picked in rows, -1 when cancelled. Falls back to a plain list when the window cannot open."""
    try:
        window = Picker('script-aeon-fonts.xml', skin_dir(), 'default', '1080i')
        window.setup(heading, section, rows, current)
        window.doModal()
        picked = window.picked
        del window
        return picked
    except Exception as error:
        xbmc.log('script.aeon.helper: font picker: %r' % (error,), xbmc.LOGWARNING)
        return xbmcgui.Dialog().select(heading, [row[0] for row in rows], preselect=current)


def number(known, family):
    """Preview number of a family: 0 follows the font set."""
    return known.index(family) + 1 if family in known else 0


def set_choice(key, value):
    if value:
        xbmc.executebuiltin('Skin.SetString(aeon.font.%s,%s)' % (key, value))
    else:
        xbmc.executebuiltin('Skin.Reset(aeon.font.%s)' % key)


def pick():
    """Font combinations first (each with a mock-up in its two fonts); the last row opens the per-section list."""
    if xbmc.getSkinDir() != SKIN:
        return
    source = read()
    known = fonts.families(source)
    ok = set(installed(source))
    presets = [p for p in fonts.PRESETS if all(not family or family in ok for family in p[2:])]
    rows = [(name, number(known, heading), number(known, body)) for _key, name, heading, body in presets]
    rows.append((text(31838, 'Fonts per section'), 0, 0))
    now = fonts.preset_of(choices())
    keys = [p[0] for p in presets]
    current = keys.index(now) if now in keys else len(rows) - 1
    title = text(32423, 'Font combination')
    got = choose(title, title, rows, current)
    if got < 0:
        return
    if got < len(presets):
        _key, _name, heading, body = presets[got]
        for key, value in fonts.preset_choices(heading, body).items():
            set_choice(key, value)
        xbmc.sleep(250)                          # builtins are queued: let the strings land before they are read back
        sync()
        return
    sections(source)


def sections(source):
    known = fonts.families(source)
    follow = text(31839, 'Follow the font set')
    dialog = xbmcgui.Dialog()
    at = 0
    while True:
        now = choices()
        rows = ['%s:  [B]%s[/B]' % (text(ident, fallback), now.get(key) or follow) for key, ident, fallback in NAMES]
        at = dialog.select(text(31838, 'Fonts per section'), rows, preselect=at)
        if at < 0:
            break
        key, ident, fallback = NAMES[at]
        options = [follow] + offered(source, keep=(now.get(key),), section=key)
        current = options.index(now[key]) if now.get(key) in options else 0
        picks = [(name, number(known, name) if position else 0, number(known, name) if position else 0)
                 for position, name in enumerate(options)]
        got = choose(text(31843, 'Font for: %s') % text(ident, fallback), text(ident, fallback), picks, current)
        if got < 0:
            continue
        set_choice(key, options[got] if got else '')
        xbmc.sleep(150)                          # builtins are queued: let the string land before it is read back
    sync()
