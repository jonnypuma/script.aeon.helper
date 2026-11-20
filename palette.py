# -*- coding: utf-8 -*-
"""RunScript(script.aeon.helper,palette): choose the palette of the Aeon Fuse skin.

A palette is a Kodi colour theme: one file in the skin's colors folder (defaults.xml = the "Aeon" palette). Choosing one
sets Kodi's own setting (Settings > Interface > Skin > Colours shows the same list) and Kodi reloads the colours.
A palette other than Aeon can colour the menus and the library views, the menus only or the library views only (skin
0.40.4): a colour file per choice ("Nord", "Nord (menus)", "Nord (library)"), see resources/lib/palscope.py.
RunScript(script.aeon.helper,palscope) asks only where the palette in use applies."""
import json
import os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib import palettestyle, palscope

SKIN = 'skin.aeon.fuse'
DEFAULT = 'SKINDEFAULT'


def rpc(method, params):
    reply = xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}))
    return json.loads(reply)


def names():
    folder = xbmcvfs.translatePath('special://home/addons/%s/colors/' % SKIN)
    found = sorted(os.path.splitext(name)[0] for name in os.listdir(folder) if name.lower().endswith('.xml') and name.lower() not in ('defaults.xml', 'fused glass.xml'))
    return [name for name in found if not palscope.is_variant(name)]


def read_colours(name):
    """The colours a palette file sets (colors/<name>.xml), as {name: aarrggbb}."""
    path = xbmcvfs.translatePath('special://home/addons/%s/colors/%s.xml' % (SKIN, name))
    try:
        with open(path, 'r') as handle:
            return palettestyle.parse(handle.read())
    except (IOError, OSError):
        return {}


def current():
    """(palette, scope) in use"""
    value = rpc('Settings.GetSettingValue', {'setting': 'lookandfeel.skincolors'}).get('result', {}).get('value', DEFAULT)
    return palscope.split(value)


def skin_text(ident, fallback):
    try:
        text = xbmcaddon.Addon(SKIN).getLocalizedString(ident)
    except RuntimeError:
        text = ''
    return text or fallback


def ask_scope(name, scope):
    """Where palette `name` applies: '', 'menus', 'library', or None when cancelled."""
    labels = [skin_text(32467, 'Menus and library views'), skin_text(32468, 'Menus only'), skin_text(32469, 'Library views only')]
    got = xbmcgui.Dialog().select('%s: %s' % (skin_text(32466, 'Use the palette for'), name), labels,
                                  preselect=palscope.SCOPES.index(scope) if scope in palscope.SCOPES else 0)
    return None if got < 0 else palscope.SCOPES[got]


def apply(name, scope):
    """Use palette `name` for `scope`: Kodi's colour setting, and the skin strings the service and the labels read."""
    value = palscope.file_for(name, scope)
    # Kodi shows new colours only by loading the skin again, and it skips that load while a dialog is open: from
    # View settings (dialog 1166) the palette was saved but never shown. Close the dialog first.
    if xbmc.getCondVisibility('Window.IsVisible(1166)'):
        xbmc.executebuiltin('Dialog.Close(1166,true)')
        monitor = xbmc.Monitor()
        for _ in range(40):
            if not xbmc.getCondVisibility('Window.IsVisible(1166) | System.HasModalDialog') or monitor.waitForAbort(0.05):
                break
    # Kodi drops the palette when the theme changes: the service puts this one back when the Aeon theme returns
    xbmc.executebuiltin('Skin.SetString(aeon.palette,%s)' % value)
    xbmc.executebuiltin('Skin.SetString(aeon.palbase,%s)' % name)
    reply = rpc('Settings.SetSettingValue', {'setting': 'lookandfeel.skincolors', 'value': value})
    if not reply.get('result'):
        rpc('Settings.SetSettingValue', {'setting': 'lookandfeel.skincolors', 'value': value + '.xml'})


def scope_only():
    """RunScript(script.aeon.helper,palscope): change only where the palette in use applies."""
    if xbmc.getSkinDir() != SKIN:
        return
    name, scope = current()
    if name == DEFAULT:
        return
    got = ask_scope(name, scope)
    if got is None or got == scope:
        return
    apply(name, got)


def pick():
    if xbmc.getSkinDir() != SKIN:
        return
    found = names()
    values = [DEFAULT] + found
    labels = ['Aeon'] + found
    now, now_scope = current()
    at = values.index(now) if now in values else 0
    # each row in its own palette's colours (DialogSelect draws them while Window(Home).Property(aeon.palpick) is set)
    items = []
    defaults = read_colours('defaults')
    for value, label in zip(values, labels):
        row = palettestyle.style(defaults, {} if value == DEFAULT else read_colours(value))
        item = xbmcgui.ListItem(label)
        for key, colour in row.items():
            item.setProperty('pal.' + key, colour)
        item.setProperty('pal.current', '1' if value == now else '')
        items.append(item)
    home = xbmcgui.Window(10000)
    home.setProperty('aeon.palpick', '1')
    try:
        got = xbmcgui.Dialog().select(xbmc.getInfoLabel('$LOCALIZE[31050]') or 'Palette', items, preselect=at)
    finally:
        home.clearProperty('aeon.palpick')
    if got < 0:
        return
    name = values[got]
    # a palette other than Aeon: for the menus and the library views, the menus only or the library views only
    scope = '' if name == DEFAULT else ask_scope(labels[got], now_scope if name == now else '')
    if scope is None or (name == now and scope == now_scope):
        return
    # the backdrop question first, while View settings is still open (it tells which view is meant); not when the
    # library keeps the Aeon colours
    if scope != 'menus':
        neutral()
    apply(name, scope)


def effective_backdrop(global_bg, view_bg, from_view_settings):
    """The backdrop the palette meets: from the View settings strip, the view's own choice (when it has one) wins
    over the global one. Returns (backdrop, 'view' | 'global')."""
    if from_view_settings and view_bg:
        return view_bg, 'view'
    return global_bg, 'global'


def neutral():
    """The library background takes the palette only with the Neutral backdrop (Fanart and Color show the artwork).
    Highlight, boxes, strips and the settings pages follow the palette with every backdrop."""
    from_view = xbmc.getCondVisibility('Window.IsVisible(1166)')
    base = xbmc.getInfoLabel('Window(Home).Property(aeon.vo.base)')
    backdrop, scope = effective_backdrop(xbmc.getInfoLabel('Skin.String(aeon.vbg)'),
                                         xbmc.getInfoLabel('Window(Home).Property(aeon.vo.bg)') if base else '', from_view)
    if backdrop in ('', 'neutral'):
        return
    text = lambda ident, fallback: xbmc.getInfoLabel('$LOCALIZE[%d]' % ident) or fallback
    if xbmcgui.Dialog().yesno(text(31050, 'Palette'), text(31934, 'The library background takes the palette only with the Neutral backdrop. '
                                                                'The highlight, boxes and strips follow it with every backdrop.[CR][CR]Use the Neutral backdrop in the libraries?'),
                              nolabel=text(31935, 'Keep the backdrop'), yeslabel=text(31936, 'Use Neutral')):
        if scope == 'view':
            xbmc.executebuiltin('Skin.SetString(%sbg,neutral)' % base)
        else:
            xbmc.executebuiltin('Skin.SetString(aeon.vbg,neutral)')
