# -*- coding: utf-8 -*-
"""RunScript(script.aeon.helper,swap,<position>,<-1|1>) moves a Home menu position up or down.
RunScript(script.aeon.helper,reset) restores the default order.
RunScript(script.aeon.helper,fonts) picks a font family per section of the skin (fontpick.py).

Skin strings cannot be swapped from the skin itself: Kodi expands every $INFO in an action list before the first
action runs, so a temporary copy is stale. Done here, one string at a time."""
import sys
import xbmc
import xbmcgui

from resources.lib import homemenu

DEFAULT = ['movies', 'tv', 'music', 'livetv', 'search', 'system', 'power', 'planner', 'off', 'off', 'off', 'off', 'off']
COUNT = homemenu.COUNT  # 24 positions (0.3.86, was 13): every preset and all ten custom items fit at once


def row_id(n):
    """Skin settings > Home menu: the row of position n (homemenu.ROWS)."""
    return homemenu.row_id(n)


def get(n):
    return xbmc.getInfoLabel('Skin.String(aeon.menu.%d)' % n) or 'off'


def put(n, value):
    xbmc.executebuiltin('Skin.SetString(aeon.menu.%d,%s)' % (n, value))


# menu key -> (label info, HideMenu setting that hides it, or '')
ITEMS = [
    ('movies', '$VAR[Aeon_Name_movies]', 'Movies'),
    ('tv', '$VAR[Aeon_Name_tv]', 'TVShows'),
    ('livetv', '$VAR[Aeon_Name_livetv]', 'LiveTV'),
    ('music', '$VAR[Aeon_Name_music]', 'Music'),
    ('search', '$VAR[Aeon_Name_search]', 'Search'),
    ('system', '$VAR[Aeon_Name_system]', ''),
    ('power', '$VAR[Aeon_Name_power]', 'Power'),
    ('sets', '$VAR[Aeon_Name_sets]', ''),
    ('favourites', '$VAR[Aeon_Name_favourites]', ''),
    ('pictures', '$VAR[Aeon_Name_pictures]', ''),
    ('addons', '$VAR[Aeon_Name_addons]', ''),
    ('weather', '$VAR[Aeon_Name_weather]', ''),
    ('planner', '$VAR[Aeon_Name_planner]', ''),
    ('files', '$VAR[Aeon_Name_files]', ''),
] + [(key, 'Custom item %s' % homemenu.custom_number(key), '') for key in homemenu.custom_keys()]


def hidden(n):
    return bool(xbmc.getCondVisibility('Skin.HasSetting(aeon.menu.hide.%d)' % n))


def set_hidden(n, value):
    xbmc.executebuiltin(('Skin.SetBool(aeon.menu.hide.%d)' if value else 'Skin.Reset(aeon.menu.hide.%d)') % n)


def old_hide_setting(key):
    """The Kodi-style HideMenu.<X> setting some items also have ('' for the others)."""
    for name, _label, hide in ITEMS:
        if name == key:
            return hide
    return ''


def swap(a, b):
    """Move the item of position a to position b (its neighbour). The highlight stays on the Move button, so it can be
    pressed again; the selected position follows the item."""
    if not (1 <= a <= COUNT and 1 <= b <= COUNT):
        return
    va, vb = get(a), get(b)
    ha, hb = hidden(a), hidden(b)
    put(a, vb)
    put(b, va)
    set_hidden(a, hb)
    set_hidden(b, ha)
    xbmc.executebuiltin('SetProperty(aeon.editslot,%d,home)' % b)
    xbmc.executebuiltin('SetProperty(aeon.editrow,%d,home)' % row_id(b))


def toggle(n):
    """Enable / Disable: show or hide the item of a position. Its type and all its settings stay as they are.
    An empty position has nothing to show: the type is asked for instead."""
    if not 1 <= n <= COUNT:
        return
    key = get(n)
    if key == 'off':
        choose(n)
        return
    old = old_hide_setting(key)
    was_hidden = hidden(n) or bool(old and xbmc.getCondVisibility('Skin.HasSetting(HideMenu.%s)' % old))
    if was_hidden:
        set_hidden(n, False)
        if old:
            xbmc.executebuiltin('Skin.Reset(HideMenu.%s)' % old)
    else:
        set_hidden(n, True)


SETS_PATH = 'library://video/movies/sets.xml/'


def sets_item(customs, used):
    """Movie sets with a spotlight: the plain preset has none, a custom item has. Returns the custom item that already
    opens the sets, or a free one set up for them ('' when all ten are taken: the preset is used then)."""
    free = [key for key in customs if key not in used]
    for key in free:
        if 'movies/sets' in xbmc.getInfoLabel('Skin.String(CustomMenu.%s.Path)' % homemenu.custom_number(key)):
            return key
    for key in free:
        number = homemenu.custom_number(key)
        if not xbmc.getInfoLabel('Skin.String(CustomMenu.%s.Path)' % number):
            label = xbmc.getInfoLabel('$VAR[Aeon_Name_sets]') or 'Movie sets'
            xbmc.executebuiltin('Skin.SetString(CustomMenu.%s.Label,%s)' % (number, label))
            xbmc.executebuiltin('Skin.SetString(CustomMenu.%s.Path,%s)' % (number, SETS_PATH))
            xbmc.executebuiltin('Skin.SetString(CustomMenu.%s.Target,videos)' % number)
            return key
    return ''


def text(ident, fallback):
    return xbmc.getInfoLabel('$LOCALIZE[%d]' % ident) or fallback


def skin_text(ident, fallback):
    """a skin string of 32000 and up (Kodi 22 reads those only as the skin add-on's own strings)"""
    try:
        import xbmcaddon
        return xbmcaddon.Addon('skin.aeon.fuse').getLocalizedString(ident) or fallback
    except Exception:
        return fallback


def pick_type(n, heading, current='off', empty=True):
    """The type picker of Choose type and Add item: the presets that are not on the menu yet, Custom item (the first
    free one of the ten, each keeps its own path, spotlight and lists), and with empty=True Empty position.
    Returns the key, or '' when nothing is to change."""
    used = set(get(i) for i in range(1, COUNT + 1) if i != n)
    presets = [it for it in ITEMS if not it[0].startswith('custom') and it[0] not in used]
    customs = homemenu.custom_keys()
    free_custom = current if current.startswith('custom') else next((key for key in customs if key not in used), '')
    keys = [it[0] for it in presets]
    labels = [xbmc.getInfoLabel(it[1]) or it[0] for it in presets]
    keys.append(free_custom or 'nocustom')
    labels.append(text(31909, 'Custom item'))
    if empty:
        keys.append('off')
        labels.append(text(31910, 'Empty position'))
    preselect = keys.index(current) if current in keys else -1
    picked = xbmcgui.Dialog().select(heading, labels, preselect=preselect)
    if picked < 0:
        return ''
    key = keys[picked]
    if key == 'sets':
        key = sets_item(customs, used) or key
    if key == 'nocustom':
        xbmcgui.Dialog().ok(text(31909, 'Custom item'), text(31912, 'All ten custom items are in use. Free one first.'))
        return ''
    return key


def place(n, key):
    put(n, key)
    set_hidden(n, False)
    old = old_hide_setting(key)
    if old:
        xbmc.executebuiltin('Skin.Reset(HideMenu.%s)' % old)


def focus_when_shown(control):
    """Skin settings: focus a row once Kodi shows it (a row appears a frame after its position is set)"""
    monitor = xbmc.Monitor()
    for _ in range(40):
        if xbmc.getCondVisibility('Control.IsVisible(%d)' % control):
            break
        if monitor.waitForAbort(0.05):
            return
    xbmc.executebuiltin('SetFocus(%d)' % control)


def positions():
    return [get(i) for i in range(1, COUNT + 1)]


def count(now=None):
    """Skin settings > Home menu: the positions in use, shown on the Add item row (n / 24). now: the positions as just
    set (Kodi applies Skin.SetString a moment later, so reading them back at once gives the old values)."""
    xbmcgui.Window(10000).setProperty('aeon.menucount', str(homemenu.used_count(now or positions())))


def choose(n):
    """Choose type: a preset that is not on the menu yet, a custom item, or nothing."""
    if not 1 <= n <= COUNT:
        return
    key = pick_type(n, text(31911, 'Type of position') + ' %d' % n, get(n))
    if not key:
        return
    now = positions()
    now[n - 1] = key
    place(n, key)
    count(now)
    if key == 'off' and homemenu.is_tail(now, n):
        # the editor hides the rows after the last item, this one too now: the focus goes to Add item
        xbmc.executebuiltin('SetProperty(aeon.editrow,%d,home)' % homemenu.ADD_ROW)
        focus_when_shown(homemenu.ADD_ROW)


def add():
    """Add item: the type picker for the first free position at the end of the menu; the new item's row takes the
    focus, so its buttons are one Right away."""
    now = positions()
    n = homemenu.add_target(now)
    if not n:
        from resources.lib.lang import L
        xbmcgui.Dialog().ok(skin_text(32591, 'Add item'), L(32022) % COUNT)
        return
    key = pick_type(n, skin_text(32591, 'Add item'), 'off', empty=False)
    if not key:
        return
    now[n - 1] = key
    place(n, key)
    count(now)
    xbmc.executebuiltin('SetProperty(aeon.editslot,%d,home)' % n)
    xbmc.executebuiltin('SetProperty(aeon.editrow,%d,home)' % row_id(n))
    focus_when_shown(row_id(n))
    # Add item again, then the new row: the list scrolls to its end, so Add item stays in view under the new row.
    # The pauses let the list take the new row into its length first.
    monitor = xbmc.Monitor()
    if monitor.waitForAbort(0.3):
        return
    xbmc.executebuiltin('SetFocus(%d)' % homemenu.ADD_ROW)
    if monitor.waitForAbort(0.15):
        return
    xbmc.executebuiltin('SetFocus(%d)' % row_id(n))


CUSTOM_STRINGS = ('CustomMenu.%s.Label', 'CustomMenu.%s.Path', 'CustomMenu.%s.Target', 'CustomMenu.%s.Addon')
CUSTOM_KEYED = ('aeon.icon.%s', 'aeon.vbg.%s', 'aeon.sp2.%s.label', 'aeon.sp2.%s.limit', 'aeon.sp2.%s.path',
                'aeon.sp2.%s.reverse', 'aeon.sp2.%s.secs', 'aeon.sp2.%s.sort')


def delete(n):
    """Delete (skin 0.56.53, helper 0.3.115): a custom item only (presets stay; the skin's button is dimmed for them).
    Asks, then clears the custom item (name, path, icon, spotlight, backdrop, widgets, submenu) and moves the items
    below it up one place; the selection stays on the same place, now the next item (or Add item at the end)."""
    if not 1 <= n <= COUNT:
        return
    key = get(n)
    k = homemenu.custom_number(key)
    if not k:
        return
    name = xbmc.getInfoLabel('Skin.String(CustomMenu.%s.Label)' % k) or 'Custom item %s' % k
    question = skin_text(32795, 'Delete %s? Its name, path, icon, widgets and submenu are removed; the items below it move up one place.')
    try:
        question = question % name
    except (TypeError, ValueError):
        pass
    if not xbmcgui.Dialog().yesno(xbmc.getLocalizedString(117), question):
        return
    # the focus goes back to the row first: once the item below moves up, Delete may be disabled (a preset), and Kodi
    # would hand the focus to the category list, which switches the page (box test 2026-11-19)
    xbmc.executebuiltin('SetProperty(aeon.skincat,homemenu,home)')
    xbmc.executebuiltin('SetFocus(%d)' % row_id(n))
    xbmc.Monitor().waitForAbort(0.2)
    before = positions()
    was = [hidden(i) for i in range(1, COUNT + 1)]
    now, hid = homemenu.remove(before, was, n)
    # only what changes: every skin setting written makes Kodi save and refresh (the first version wrote all 24
    # positions and flags and was slow, user 2026-11-19)
    for i in homemenu.changed(before, now):
        put(i, now[i - 1])
    for i in homemenu.changed(was, hid):
        set_hidden(i, hid[i - 1])
    for name_ in [x % k for x in CUSTOM_STRINGS] + [x % key for x in CUSTOM_KEYED]:
        if xbmc.getInfoLabel('Skin.String(%s)' % name_):
            xbmc.executebuiltin('Skin.Reset(%s)' % name_)
    if xbmc.getCondVisibility('Skin.HasSetting(aeon.nosp2.%s)' % key):
        xbmc.executebuiltin('Skin.Reset(aeon.nosp2.%s)' % key)
    try:
        import menufile
        menufile.clear_custom(int(k))
    except Exception as error:
        xbmc.log('[script.aeon.helper] delete custom item: %s' % error, xbmc.LOGINFO)
    count(now)
    if homemenu.is_tail(now, n):
        xbmc.executebuiltin('SetProperty(aeon.editrow,%d,home)' % homemenu.ADD_ROW)
        focus_when_shown(homemenu.ADD_ROW)
    else:
        xbmc.executebuiltin('SetProperty(aeon.editslot,%d,home)' % n)
        xbmc.executebuiltin('SetProperty(aeon.editrow,%d,home)' % row_id(n))
        focus_when_shown(row_id(n))


def enable(n):
    choose(n)


def icon(n):
    """Choose icon: a grid of icons for the item of position n (the select dialog draws a grid while the Home property
    aeon.iconpick is set). The first tile is the item's own icon ('Default'); the pick is kept per item key."""
    import xbmcvfs
    from resources.lib import menuicons
    if not 1 <= n <= COUNT:
        return
    key = get(n)
    if key == 'off':
        return
    custom_path = xbmc.getInfoLabel('Skin.String(CustomMenu.%s.Path)' % homemenu.custom_number(key)) if key.startswith('custom') else ''
    own = menuicons.default_icon(key, custom_path)
    skin_files = xbmcvfs.listdir('special://skin/media/' + menuicons.SKIN_DIR)[1]
    af3_files = xbmcvfs.listdir('special://skin/media/' + menuicons.AF3_DIR)[1]
    entries = [(xbmc.getLocalizedString(571) or 'Default', '')] + menuicons.choices(skin_files, af3_files)
    current = xbmc.getInfoLabel('Skin.String(aeon.icon.%s)' % key)
    items = []
    for label, path in entries:
        item = xbmcgui.ListItem(label, offscreen=True)
        item.setArt({'icon': path or own, 'thumb': path or own})
        items.append(item)
    home = xbmcgui.Window(10000)
    home.setProperty('aeon.iconpick', '1')
    try:
        picked = xbmcgui.Dialog().select(xbmc.getLocalizedString(19284) or 'Choose icon', items,
                                         preselect=menuicons.preselect(entries, current), useDetails=True)
    finally:
        home.clearProperty('aeon.iconpick')
    if picked < 0:
        return
    path = entries[picked][1]
    if path:
        xbmc.executebuiltin('Skin.SetString(aeon.icon.%s,%s)' % (key, path))
    else:
        xbmc.executebuiltin('Skin.Reset(aeon.icon.%s)' % key)


def reset():
    now = [DEFAULT[n - 1] if n <= len(DEFAULT) else 'off' for n in range(1, COUNT + 1)]
    for n, value in enumerate(now, 1):
        put(n, value)
        set_hidden(n, False)
    count(now)


def ctx(args):
    """Skin settings > Context menu: ctx,toggle,<place> switches the item at that place on / off; ctx,move,<-1|1>,<place>
    moves it, and the page's selection follows it."""
    from resources.lib import ctxmenu
    order = ctxmenu.read_order([xbmc.getInfoLabel('Skin.String(aeon.ctx.pos%d)' % n) for n in range(1, 5)])
    try:
        place = int(args[-1])
    except ValueError:
        return
    if not 1 <= place <= len(order):
        return
    if args[0] == 'toggle':
        setting, _inverted = ctxmenu.SWITCH[order[place - 1]]
        on = xbmc.getCondVisibility('Skin.HasSetting(%s)' % setting)
        xbmc.executebuiltin('Skin.%s(%s)' % ('Reset' if on else 'SetBool', setting))
    elif args[0] == 'move' and len(args) >= 3:
        try:
            delta = int(args[1])
        except ValueError:
            return
        new, place = ctxmenu.moved(order, place, delta)
        for n, action in enumerate(new, 1):
            xbmc.executebuiltin('Skin.SetString(aeon.ctx.pos%d,%s)' % (n, action))
        home = xbmcgui.Window(10000)
        home.setProperty('aeon.ctxslot', str(place))
        home.setProperty('aeon.ctxrow', str(ctxmenu.FIRST_ROW + place - 1))


def wizard_menu(key):
    """Setup wizard > Home menu items: switch a preset on or off. On: show it where it is, or put it in the first
    empty position; off: hide it (its position and settings stay)."""
    from resources.lib import wizard
    if key not in [name for name, _label, _hide in ITEMS]:
        return
    positions = [get(n) for n in range(1, COUNT + 1)]
    old = old_hide_setting(key)
    hides = [hidden(n) or bool(old and positions[n - 1] == key and xbmc.getCondVisibility('Skin.HasSetting(HideMenu.%s)' % old))
             for n in range(1, COUNT + 1)]
    what, n = wizard.menu_switch(positions, hides, key)
    if what == 'hide':
        set_hidden(n, True)
    elif what in ('show', 'place'):
        if what == 'place':
            put(n, key)
        set_hidden(n, False)
        if old:
            xbmc.executebuiltin('Skin.Reset(HideMenu.%s)' % old)
    else:
        from resources.lib.lang import L
        xbmcgui.Dialog().notification(L(32021), L(32022) % COUNT, xbmcgui.NOTIFICATION_INFO, 4000)


def album_view():
    """Music OSD > Album: the album of the song that plays, in the music library. The controls are a modal dialog and
    so is the lyrics window of CU LRC Lyrics; Kodi opens no window over them, so they close first."""
    import json
    songid = xbmc.getInfoLabel('MusicPlayer.DBID')
    if not songid.isdigit() or int(songid) <= 0:
        return
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': 'AudioLibrary.GetSongDetails',
        'params': {'songid': int(songid), 'properties': ['albumid']}})))
    albumid = ((reply.get('result') or {}).get('songdetails') or {}).get('albumid')
    if not albumid:
        return
    xbmc.executebuiltin('Dialog.Close(all,true)')
    monitor = xbmc.Monitor()
    for _ in range(40):
        if not xbmc.getCondVisibility('System.HasModalDialog') or monitor.waitForAbort(0.1):
            break
    xbmc.executebuiltin('ActivateWindow(Music,musicdb://albums/%d/,return)' % int(albumid))


def wizard_rpc(method, params):
    import json
    return json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})))


def wizard_now():
    """what runs now, in the wizard's terms (theme, menutheme, fgmenu, palette = Kodi's colours)"""
    from resources.lib import wizard
    colours = (wizard_rpc('Settings.GetSettingValue', {'setting': 'lookandfeel.skincolors'}).get('result') or {}).get('value', '')
    if xbmc.getCondVisibility('Skin.HasSetting(aeon.fglass)'):
        theme = 'fused'
    elif xbmc.getCondVisibility('Skin.HasSetting(aeon.vglass)'):
        theme = 'glass'
    else:
        theme = wizard.theme_key(xbmc.getInfoLabel('Skin.CurrentTheme'))
    return {'theme': theme, 'menutheme': xbmc.getInfoLabel('Skin.String(aeon.menutheme)'),
            'fgmenu': xbmc.getInfoLabel('Skin.String(aeon.fgmenu)'), 'palette': colours}


def open_wizard():
    """Home (first run) and Skin settings > Setup wizard (skin 0.56.40): publish what the wizard starts from, then open
    it (dialog 1173). Done here, in order: the dialog's own onload actions run later than their conditions are read.
    aeon.wiz.theme / menutheme / fgmenu / palette are the wizard's choices of what waits for Finish; palchanged and
    fontchanged say a palette or fonts were picked; page is the page shown."""
    from resources.lib import wizard
    if xbmc.getSkinDir() != 'skin.aeon.fuse' or xbmc.getCondVisibility('Window.IsVisible(1173)'):
        return
    now = wizard_now()
    palette = wizard.palette_name(now['palette'])
    if now['theme'] != 'aeon' or palette == 'Fused Glass':
        # the colours of Aeon Glass / Fused Glass are not a palette: the one the Aeon theme keeps
        palette = xbmc.getInfoLabel('Skin.String(aeon.palette)') or wizard.DEFAULT
    import palette as palettes
    home = xbmcgui.Window(10000)
    for prop in ('pw', 'pk', 'pk2', 'pa', 'palchanged', 'fontchanged', 'reload'):
        home.clearProperty('aeon.wiz.%s' % prop)
    home.setProperty('aeon.wiz.theme', now['theme'])
    home.setProperty('aeon.wiz.menutheme', now['menutheme'])
    home.setProperty('aeon.wiz.fgmenu', now['fgmenu'])
    home.setProperty('aeon.wiz.palette', palette)
    # the palette step: the palette in use (pal0, against which a new pick counts) and its place in the list
    home.setProperty('aeon.wiz.pal0', palette)
    home.setProperty('aeon.wiz.palidx', str(wizard.palette_index(palette, palettes.names())))
    home.setProperty('aeon.wiz.step', '1')
    try:
        import fontpick
        home.setProperty('aeon.wiz.font', fontpick.font_name())
        from resources.lib import fonts
        home.setProperty('aeon.wiz.fontkey', fonts.preset_of(fontpick.choices()))
    except Exception as error:                       # a missing Font.xml must not keep the wizard shut
        xbmc.log('script.aeon.helper: wizard font name: %r' % (error,), xbmc.LOGWARNING)
    home.setProperty('aeon.wiz.page', 'theme')
    xbmc.executebuiltin('ActivateWindow(1173)')


def wizard_palette():
    """Setup wizard > Look > Palette: Kodi's list of the palettes (each with its picture); the choice waits for Finish"""
    import palette
    from resources.lib import wizard
    home = xbmcgui.Window(10000)
    names = [wizard.DEFAULT] + sorted(palette.names())
    pictures = 'special://home/addons/skin.aeon.fuse/media/aeon/wizard/pal_%s.png'
    items = []
    for name in names:
        item = xbmcgui.ListItem('Aeon' if name == wizard.DEFAULT else name)
        art = pictures % ('defaults' if name == wizard.DEFAULT else name)
        item.setArt({'icon': art, 'thumb': art})
        items.append(item)
    current = home.getProperty('aeon.wiz.palette') or wizard.DEFAULT
    got = xbmcgui.Dialog().select(xbmc.getInfoLabel('$LOCALIZE[31050]') or 'Palette', items,
                                  preselect=names.index(current) if current in names else 0, useDetails=True)
    if got < 0:
        return
    home.setProperty('aeon.wiz.palette', names[got])
    if names[got] != wizard.palette_name(wizard_now()['palette']):
        home.setProperty('aeon.wiz.palchanged', '1')
    else:
        home.clearProperty('aeon.wiz.palchanged')


def wizard_defaults(finish):
    """Setup wizard > Start: the chosen theme's defaults (resources/lib/wizard.DEFAULTS): its settings change at once,
    its Skin style and palette become the wizard's choices; with finish, Finish follows."""
    from resources.lib import wizard
    home = xbmcgui.Window(10000)
    theme = home.getProperty('aeon.wiz.theme') or 'fused'
    calls, later = wizard.defaults(theme)
    for call in calls:
        xbmc.executebuiltin(call)
    for key, value in later.items():
        home.setProperty('aeon.wiz.%s' % key, value)
    if 'palette' in later:
        if later['palette'] != wizard.palette_name(wizard_now()['palette']):
            home.setProperty('aeon.wiz.palchanged', '1')
        else:
            home.clearProperty('aeon.wiz.palchanged')
    if finish:
        xbmc.sleep(300)                              # builtins are queued: let the settings land first
        finish_wizard()


def finish_wizard():
    """Setup wizard (dialog 1173) > Finish: mark it done, then apply what waited (Skin style, palette, fonts, theme) and
    restart Kodi (a skin reload alone leaves skin settings misread until the next start)."""
    from resources.lib import skinstyle, wizard
    home = xbmcgui.Window(10000)
    want = dict((key, home.getProperty('aeon.wiz.%s' % key)) for key in ('theme', 'menutheme', 'fgmenu', 'palette'))
    fonts_changed = bool(home.getProperty('aeon.wiz.fontchanged'))
    # the focus highlight (Fused Glass) takes its pictures when the skin loads
    reload_wanted = bool(home.getProperty('aeon.wiz.reload'))
    xbmc.executebuiltin('Skin.SetBool(aeon.wizard.done)')
    xbmc.executebuiltin('Dialog.Close(1173)')
    monitor = xbmc.Monitor()
    for _ in range(40):
        if not xbmc.getCondVisibility('Window.IsVisible(1173)') or monitor.waitForAbort(0.05):
            break
    steps = wizard.plan(want, wizard_now())
    for what, value in steps:
        if what == 'menutheme':
            xbmc.executebuiltin('Skin.SetString(aeon.menutheme,%s)' % value if value else 'Skin.Reset(aeon.menutheme)')
        elif what == 'fgmenu':
            xbmc.executebuiltin('Skin.SetString(aeon.fgmenu,%s)' % value if value else 'Skin.Reset(aeon.fgmenu)')
            call = skinstyle.builtin(value, xbmc.getInfoLabel('Skin.String(aeon.fgmat)'))
            if call:
                xbmc.executebuiltin(call)
        elif what == 'palette':
            xbmc.executebuiltin('Skin.SetString(aeon.palette,%s)' % value)
            xbmc.executebuiltin('Skin.SetString(aeon.palbase,%s)' % value)
            if not wizard_rpc('Settings.SetSettingValue', {'setting': 'lookandfeel.skincolors', 'value': value}).get('result'):
                wizard_rpc('Settings.SetSettingValue', {'setting': 'lookandfeel.skincolors', 'value': value + '.xml'})
        elif what == 'theme':
            # the service follows the theme with these switches; set first, so it has nothing to reload
            fused, glass = value == 'fused', value in ('fused', 'glass')
            xbmc.executebuiltin('Skin.SetBool(aeon.fglass)' if fused else 'Skin.Reset(aeon.fglass)')
            xbmc.executebuiltin('Skin.SetBool(aeon.vglass)' if glass else 'Skin.Reset(aeon.vglass)')
            monitor.waitForAbort(0.3)
            wizard_rpc('Settings.SetSettingValue', {'setting': 'lookandfeel.skintheme', 'value': wizard.KODI_THEME[value]})
        monitor.waitForAbort(0.5)
    if fonts_changed:
        import fontpick
        try:
            fontpick.apply()
        except Exception as error:
            xbmc.log('script.aeon.helper: wizard fonts: %r' % (error,), xbmc.LOGWARNING)
    if not steps and not fonts_changed and not reload_wanted:
        return
    platform = next((name for name in ('android', 'windows', 'osx', 'linux')
                     if xbmc.getCondVisibility('System.Platform.%s' % name)), '')
    if wizard.can_restart(platform):
        monitor.waitForAbort(1.0)
        xbmc.executebuiltin('RestartApp')
    elif not any(what == 'theme' for what, _value in steps):
        # elsewhere a new theme loads the skin by itself; the rest needs it loaded once
        xbmc.executebuiltin('ReloadSkin()')


def epg_reload():
    """EPG tools > Reload EPG (0.3.87). Kodi has no command to fetch the guide again, so the enabled PVR client add-ons
    are switched off and on: each then loads its channels and guide afresh. That ends live TV, so the playing channel
    is noted first and opened again once Kodi has its channels back."""
    import json
    monitor = xbmc.Monitor()

    def rpc(method, params=None):
        request = {'jsonrpc': '2.0', 'id': 1, 'method': method}
        if params is not None:
            request['params'] = params
        return json.loads(xbmc.executeJSONRPC(json.dumps(request))).get('result') or {}

    xbmc.executebuiltin('Dialog.Close(pvrguidecontrols,true)')
    clients = [a['addonid'] for a in rpc('Addons.GetAddons', {'type': 'kodi.pvrclient', 'enabled': True}).get('addons', [])]
    if not clients:
        return
    channel = None
    for player in rpc('Player.GetActivePlayers') or []:
        item = rpc('Player.GetItem', {'playerid': player['playerid']}).get('item', {})
        if item.get('type') == 'channel' and item.get('id'):
            channel = item['id']
    heading = xbmc.getInfoLabel('$ADDON[skin.aeon.fuse 32593]') or 'Reload EPG'
    xbmcgui.Dialog().notification(heading, xbmc.getLocalizedString(20186), xbmcgui.NOTIFICATION_INFO, 5000)
    for addon in clients:
        rpc('Addons.SetAddonEnabled', {'addonid': addon, 'enabled': False})
    if monitor.waitForAbort(2):
        return
    for addon in clients:
        rpc('Addons.SetAddonEnabled', {'addonid': addon, 'enabled': True})
    # wait until Kodi has channels again (up to a minute), then put the channel back
    for _ in range(120):
        if monitor.waitForAbort(0.5):
            return
        if xbmc.getCondVisibility('PVR.HasTVChannels | PVR.HasRadioChannels'):
            break
    if channel:
        if monitor.waitForAbort(2):
            return
        rpc('Player.Open', {'item': {'channelid': channel}})


def epg_group():
    """EPG tools > Channel group (0.3.60): close the tools card at once, open Kodi's group list on the guide, and once
    a new group has loaded go to its first channel with the focus on the grid (id 50). Run from here so every step
    waits for the one before; from the skin the card's close and the group list overlapped. Cancel: back to the grid."""
    monitor = xbmc.Monitor()
    xbmc.executebuiltin('Dialog.Close(pvrguidecontrols,true)')
    for _ in range(40):
        if not xbmc.getCondVisibility('Window.IsActive(pvrguidecontrols)'):
            break
        if monitor.waitForAbort(0.05):
            return
    if not xbmc.getCondVisibility('Window.IsActive(TVGuide) | Window.IsActive(RadioGuide)'):
        return
    # the guide shows no group name (its label 29 says "Timeline"): a new group shows as another channel count or
    # another selected channel in the grid
    def grid():
        return (xbmc.getInfoLabel('Container(50).NumItems'), xbmc.getInfoLabel('Container(50).ListItem.ChannelName'))
    before = grid()
    xbmc.executebuiltin('PVR.EpgGridControl(SelectGroup)', True)
    # the group list is modal: wait for it to open (up to 1 s, it may have come and gone while the call waited) and close
    for _ in range(10):
        if xbmc.getCondVisibility('Window.IsActive(selectdialog)'):
            break
        if monitor.waitForAbort(0.1):
            return
    for _ in range(3000):
        if not xbmc.getCondVisibility('Window.IsActive(selectdialog)'):
            break
        if monitor.waitForAbort(0.1):
            return
    if not xbmc.getCondVisibility('Window.IsActive(TVGuide) | Window.IsActive(RadioGuide)'):
        return
    changed = False
    for _ in range(80):             # the guide reloads the new group in the background
        if grid() != before and not xbmc.getCondVisibility('Container(50).IsUpdating') and \
                xbmc.getCondVisibility('Integer.IsGreater(Container(50).NumItems,0)'):
            changed = True
            break
        if monitor.waitForAbort(0.1):
            return
    if changed:
        monitor.waitForAbort(0.3)
        xbmc.executebuiltin('PVR.EpgGridControl(FirstChannel)', True)
    xbmc.executebuiltin('SetFocus(50)')


def np_artist():
    """the strip's Now playing panel (skin 0.56.42) > the artist: the playing song's (first) artist opened in the music
    library, else the artists list"""
    import json
    import xbmc

    def rpc(method, params=None):
        request = {'jsonrpc': '2.0', 'id': 1, 'method': method}
        if params is not None:
            request['params'] = params
        return json.loads(xbmc.executeJSONRPC(json.dumps(request))).get('result') or {}

    players = [p for p in (rpc('Player.GetActivePlayers') or []) if p.get('type') == 'audio']
    ids = []
    if players:
        item = rpc('Player.GetItem', {'playerid': players[0]['playerid'], 'properties': ['artistid', 'albumartistid']}).get('item') or {}
        ids = item.get('artistid') or item.get('albumartistid') or []
    if ids:
        xbmc.executebuiltin('ActivateWindow(Music,musicdb://artists/%d/,return)' % int(ids[0]))
    else:
        xbmc.executebuiltin('ActivateWindow(Music,musicdb://artists/,return)')


def main(argv):
    if not argv:
        return
    if argv[0] == 'swap' and len(argv) >= 3:
        pos = int(argv[1])
        swap(pos, pos + int(argv[2]))
    elif argv[0] == 'enable' and len(argv) >= 2:
        enable(int(argv[1]))
    elif argv[0] == 'toggle' and len(argv) >= 2 and argv[1].isdigit():
        toggle(int(argv[1]))
    elif argv[0] == 'type' and len(argv) >= 2 and argv[1].isdigit():
        choose(int(argv[1]))
    elif argv[0] == 'add':
        add()
    elif argv[0] == 'delete' and len(argv) >= 2 and argv[1].isdigit():
        delete(int(argv[1]))
    elif argv[0] == 'count':
        count()
    elif argv[0] == 'icon' and len(argv) >= 2 and argv[1].isdigit():
        icon(int(argv[1]))
    elif argv[0] == 'epggroup':
        epg_group()
    elif argv[0] == 'epgreload':
        epg_reload()
    elif argv[0] == 'albumview':
        album_view()
    elif argv[0] == 'reset':
        reset()
    elif argv[0] == 'fonts':
        # fonts,wizard / fonts,set,<preset> (setup wizard, skin 0.56.40): the choice waits for Finish (no skin reload
        # while the wizard is open)
        import fontpick
        if len(argv) >= 3 and argv[1] == 'set':
            fontpick.set_preset(argv[2])
        else:
            fontpick.pick(wizard=len(argv) >= 2 and argv[1] == 'wizard')
    elif argv[0] == 'picshow':
        # Home > Pictures, OK on the menu item (skin 0.56.21): a slideshow of the newest folder. main() imports xbmc and
        # xbmcgui further down, so the bare names are local to it: import what is needed here under other names.
        # 0.3.109: the slideshow starts from the Pictures window, not over Home. Kodi runs SlideShow() inside its message
        # handler with the GUI lock held for the whole show and still processes the window underneath: a Home list that
        # was loading and changed its path then waited for that lock while the screen waited for the list (box froze
        # twice on 2026-11-18, OK on Pictures). The Pictures window has no such lists.
        from xbmc import executebuiltin as run_builtin, getCondVisibility as has, Monitor as Waiter
        from xbmcgui import Window as HomeWindow
        where = HomeWindow(10000).getProperty('aeon.pic.folder')
        if where:
            quoted = where.replace('"', '\\"')
            run_builtin('ActivateWindow(Pictures,"%s",return)' % quoted)
            waiter = Waiter()
            for _ in range(80):
                if has('Window.IsActive(pictures) + !Container.IsUpdating') or waiter.waitForAbort(0.1):
                    break
            if has('Window.IsActive(pictures)') and not waiter.waitForAbort(0.3):
                run_builtin('SlideShow("%s")' % quoted)
        else:
            run_builtin('ActivateWindow(Pictures)')
    elif argv[0] == 'chippick':
        import chippick
        chippick.pick()
    elif argv[0] == 'lib' and len(argv) >= 3:
        import remotelib
        remotelib.run(argv[1], argv[2])
    elif argv[0] == 'libremote' and len(argv) >= 2:
        import remotelib
        remotelib.setting(argv[1])
    elif argv[0] == 'addonrec':
        import addonrec
        if len(argv) > 1 and argv[1] == 'count':
            addonrec.count()
        elif len(argv) > 1 and argv[1] == 'batch':
            addonrec.batch()
        else:
            addonrec.show()
    elif argv[0] == 'placepick':
        import placepick
        placepick.pick(argv[1] if len(argv) > 1 else '')
    elif argv[0] == 'cinemacountry':
        import cinemacountry
        cinemacountry.pick()
    elif argv[0] == 'palette':
        import palette
        palette.pick()
    elif argv[0] == 'palscope':
        import palette
        palette.scope_only()
    elif argv[0] == 'ctx' and len(argv) >= 3:
        ctx(argv[1:])
    elif argv[0] == 'rescan':
        # after the add-on's files were replaced by hand: make Kodi read addon.xml again
        import xbmc
        xbmc.executebuiltin('UpdateLocalAddons')
    elif argv[0] == 'npartist':
        np_artist()
    elif argv[0] == 'settings' and len(argv) >= 2:
        # Skin settings > System > Export / Import skin settings (skin 0.56.42)
        import settingsio
        settingsio.main(argv[1], ','.join(argv[2:]) or None)
    elif argv[0] == 'artcheck':
        # Skin settings > Motion, memory, reset > Check library art now: posters / banners / landscapes / fanart of the wrong
        # shape, replaced by a picture from the same folder that fits (artguard.py)
        import artguard
        artguard.check_all()
    elif argv[0] == 'trailer' and len(argv) >= 2:
        import trailer
        trailer.main(argv[1], argv[2] if len(argv) > 2 else '')
    elif argv[0] == 'wizard':
        if len(argv) >= 2 and argv[1] == 'open':
            open_wizard()
        elif len(argv) >= 3 and argv[1] == 'menu':
            wizard_menu(argv[2])
        elif len(argv) >= 2 and argv[1] == 'palette':
            wizard_palette()
        elif len(argv) >= 2 and argv[1] == 'defaults':
            wizard_defaults(len(argv) >= 3 and argv[2] == 'finish')
        else:
            finish_wizard()
    elif argv[0] == 'arr':
        import arrfeed
        arrfeed.main()
    elif argv[0] == 'search' and len(argv) >= 2:
        import searchhist
        searchhist.run(argv[1])
    elif argv[0] == 'searchkey' and len(argv) >= 2:
        # the Fused Glass Search window's own keyboard: del, space, clear, kodi (Kodi's keyboard) (0.3.73)
        import searchwin
        searchwin.key(argv[1])
    elif argv[0] == 'theme':
        # Skin settings > Appearance > Theme: set Kodi's Theme setting to Aeon, Glass or Fused Glass (the service follows
        # it). theme,<aeon|glass|fused> picks one; theme alone steps to the next (Aeon > Glass > Fused Glass > Aeon).
        import json
        import xbmc
        names = {'aeon': 'Aeon', 'glass': 'Glass', 'fused': 'Fused Glass'}
        order = ['aeon', 'glass', 'fused']
        now = xbmc.getInfoLabel('Skin.CurrentTheme').lower()
        current = 'fused' if now.startswith('fused') else 'glass' if now.startswith('glass') else 'aeon'
        wanted = argv[1] if len(argv) >= 2 and argv[1] in names else order[(order.index(current) + 1) % len(order)]
        if wanted != current:
            # 0.3.115: the skin's own switches first. Kodi reloads the skin the moment its Theme changes; with the
            # switches still on the old theme that first load drew it (Aeon Glass for a moment before Fused Glass,
            # user 2026-11-19), and the service's sync then loaded it a second time
            fused, glass = wanted == 'fused', wanted in ('glass', 'fused')
            xbmc.executebuiltin('Skin.SetBool(aeon.fglass)' if fused else 'Skin.Reset(aeon.fglass)')
            xbmc.executebuiltin('Skin.SetBool(aeon.vglass)' if glass else 'Skin.Reset(aeon.vglass)')
            xbmc.sleep(100)
            request = {'jsonrpc': '2.0', 'id': 1, 'method': 'Settings.SetSettingValue',
                       'params': {'setting': 'lookandfeel.skintheme', 'value': names[wanted]}}
            xbmc.executeJSONRPC(json.dumps(request))
    elif argv[0] == 'focusstrip' and len(argv) >= 2 and argv[1].isdigit():
        # Home: Down on Movies / TV / Music while the strip under the menu is still loading (its path waits for its
        # own submenu list 9391N, then it loads its own titles; skin 0.56.4 shows Loading... meanwhile) or refreshing
        # (it is out of sight then): focus it as soon as it has items and is done, unless the menu moved on. Up to
        # 45 s while it is still loading (TV took 3.6-4.7 s on the box; right after Kodi starts, while a dozen add-on
        # services start, a list can wait 25 s and more); a strip that finished empty ends the wait.
        import time
        import xbmc
        strip = int(argv[1])
        node = {9301: 93911, 9302: 93912, 9303: 93913}.get(strip)
        section = xbmc.getInfoLabel('Container(9000).ListItem.Label2')
        monitor = xbmc.Monitor()
        started = time.time()
        while time.time() - started < 45:
            if monitor.waitForAbort(0.1):
                return
            if not xbmc.getCondVisibility('Control.HasFocus(9000)') or xbmc.getInfoLabel('Container(9000).ListItem.Label2') != section:
                return
            if xbmc.getCondVisibility('Integer.IsGreater(Container(%d).NumItems,0) + !Container(%d).IsUpdating' % (strip, strip)):
                xbmc.executebuiltin('SetFocus(%d)' % strip)
                return
            loading = xbmc.getCondVisibility('Container(%d).IsUpdating' % strip) or (
                node and (xbmc.getCondVisibility('Container(%d).IsUpdating' % node) or
                          not xbmc.getCondVisibility('Integer.IsGreater(Container(%d).NumItems,0)' % node)))
            if not loading and time.time() - started > 2:
                return
    elif argv[0] == 'menutheme':
        # Skin settings > Appearance > Menu theme. Skin.String(aeon.menutheme): '' = Bridge in the Aeon theme (Glass's own
        # menus in Glass), mosaic / ledger / tabslab = the Aeon theme's other menu styles, fused = Fuse.
        # The four Aeon styles are picked by include conditions that Kodi checks each time a window opens, so a change
        # between them shows on the next menu. Fuse changes button textures that only load with the skin, so going to or
        # from Fuse needs the skin loaded again. A reload leaves skin settings misread until the next start, so on boxes
        # that restart cleanly (CoreELEC / Linux) Kodi restarts instead, when the user agrees.
        import xbmc
        import xbmcgui
        from resources.lib import wizard
        cur = xbmc.getInfoLabel('Skin.String(aeon.menutheme)')
        order = ['mosaic', 'ledger', '', 'tabslab', 'fused']
        if len(argv) >= 2:
            target = '' if argv[1] in ('aeon', 'bridge') else argv[1]
        elif xbmc.getCondVisibility('Skin.HasSetting(aeon.vglass)'):
            target = '' if cur == 'fused' else 'fused'
        else:
            # OK on the row in the Aeon theme: the next option, round to the first
            target = order[(order.index(cur) + 1) % len(order)] if cur in order else ''
        if target not in order or target == cur:
            return
        xbmc.executebuiltin('Skin.SetString(aeon.menutheme,%s)' % target if target else 'Skin.Reset(aeon.menutheme)')
        if (target == 'fused') == (cur == 'fused'):
            return
        xbmc.sleep(300)
        platform = next((name for name in ('android', 'windows', 'osx', 'linux')
                         if xbmc.getCondVisibility('System.Platform.%s' % name)), '')
        if wizard.can_restart(platform):
            from resources.lib.lang import L
            if xbmcgui.Dialog().yesno(L(32023), L(32024), nolabel=L(32025), yeslabel=L(32026)):
                xbmc.executebuiltin('RestartApp')
        else:
            xbmc.executebuiltin('ReloadSkin()')
    elif argv[0] == 'skinstyle':
        # 0.3.105 (skin 0.56.29) Skin settings > Appearance > Skin style in Fused Glass: OK steps Dark -> Clear -> Frost ->
        # Fused Glass (the System-screen menus) -> Dark; the library's glass follows (aeon.fgmat). Going to or from Fused
        # Glass changes button textures that only load with the skin: Kodi starts again when the user agrees, as for Fuse.
        import xbmc
        import xbmcgui
        from resources.lib import skinstyle, wizard
        cur = xbmc.getInfoLabel('Skin.String(aeon.fgmenu)')
        # 0.3.111 (skin 0.56.45): Skin settings set a picked style; 'dark' is the Dark style ('' cannot be passed)
        arg = '' if len(argv) >= 2 and argv[1] == 'dark' else (argv[1] if len(argv) >= 2 else None)
        target = arg if arg in skinstyle.ORDER else skinstyle.next_style(cur)
        xbmc.executebuiltin('Skin.SetString(aeon.fgmenu,%s)' % target if target else 'Skin.Reset(aeon.fgmenu)')
        call = skinstyle.builtin(target, xbmc.getInfoLabel('Skin.String(aeon.fgmat)'))
        if call:
            xbmc.executebuiltin(call)
        if not skinstyle.needs_restart(cur, target):
            return
        xbmc.sleep(300)
        platform = next((name for name in ('android', 'windows', 'osx', 'linux')
                         if xbmc.getCondVisibility('System.Platform.%s' % name)), '')
        if wizard.can_restart(platform):
            from resources.lib.lang import L
            if xbmcgui.Dialog().yesno(L(32023), L(32024), nolabel=L(32025), yeslabel=L(32026)):
                xbmc.executebuiltin('RestartApp')
        else:
            xbmc.executebuiltin('ReloadSkin()')
    elif argv[0] == 'osdalbum' and len(argv) >= 2:
        # 0.3.111 (skin 0.56.45) music player controls: the arrows over the album track list
        from resources.lib import osdalbums
        osdalbums.step(argv[1])
    elif argv[0] == 'osdplay' and len(argv) >= 2:
        from resources.lib import osdalbums
        osdalbums.play(argv[1])
    elif argv[0] == 'startitem':
        # 0.3.111 (skin 0.56.45) Skin settings > Home menu > Start on: the Home menu item that has the focus when Kodi
        # starts, after the splash (service.StartItem). Default: Home as Kodi opens it.
        shown = [(i, get(i)) for i in range(1, COUNT + 1) if get(i) != 'off' and not hidden(i)]
        names = [xbmc.getInfoLabel('$VAR[Aeon_Name_%s]' % key) or key for _i, key in shown]
        now = xbmc.getInfoLabel('Skin.String(aeon.startitem)')
        keys = [key for _i, key in shown]
        pre = keys.index(now) + 1 if now in keys else 0
        heading = xbmc.getInfoLabel('$ADDON[skin.aeon.fuse 32749]') or 'Start on'
        pick = xbmcgui.Dialog().select(heading, [xbmc.getInfoLabel('$LOCALIZE[31546]') or 'Default'] + names, preselect=pre)
        if pick < 0:
            return
        if pick == 0:
            xbmc.executebuiltin('Skin.Reset(aeon.startitem)')
            xbmc.executebuiltin('Skin.Reset(aeon.startitem.label)')
        else:
            xbmc.executebuiltin('Skin.SetString(aeon.startitem,%s)' % keys[pick - 1])
            xbmc.executebuiltin('Skin.SetString(aeon.startitem.label,%s)' % names[pick - 1].replace(',', ' '))
    elif argv[0] == 'lyrics':
        # music player controls: the lyrics button steps Off -> Lines -> Words -> Off
        import xbmc
        on = xbmc.getCondVisibility('Skin.HasSetting(aeon.lyricson)')
        words = xbmc.getCondVisibility('Skin.HasSetting(aeon.lyrics.words)')
        if not on:
            xbmc.executebuiltin('Skin.SetBool(aeon.lyricson)')
            xbmc.executebuiltin('Skin.Reset(aeon.lyrics.words)')
        elif not words:
            xbmc.executebuiltin('Skin.SetBool(aeon.lyrics.words)')
        else:
            xbmc.executebuiltin('Skin.Reset(aeon.lyricson)')
    elif argv[0] == 'lyricsave':
        # Skin settings > Player > Save lyrics next to the song (CU LRC Lyrics' own settings)
        from resources.lib import lyricsave
        lyricsave.toggle()
    elif argv[0] == 'planner' and len(argv) >= 2:
        import plannerwin
        plannerwin.main(argv[1])
    elif argv[0] == 'playerfacts':
        # Fused Glass information screen: subtitle / audio languages and file size of the video playing
        import playerfacts
        playerfacts.main()
    elif argv[0] == 'chapthumbs':
        # chapters dialog: thumbnails from the Trickplay sprites next to the playing video
        import chapterwin
        chapterwin.main()
    elif argv[0] == 'android':
        # CoreELEC: boot the Android that is installed beside it
        import xbmc
        xbmc.executebuiltin('System.ExecWait("/usr/sbin/rebootfromnand")')
        xbmc.executebuiltin('Reset()')
    elif argv[0] == 'tvgroup':
        # Live TV on Home: which channel group its second row shows
        import json
        import xbmc
        import xbmcgui
        request = {'jsonrpc': '2.0', 'id': 1, 'method': 'PVR.GetChannelGroups', 'params': {'channeltype': 'tv'}}
        groups = json.loads(xbmc.executeJSONRPC(json.dumps(request))).get('result', {}).get('channelgroups') or []
        if groups:
            names = [group['label'] for group in groups]
            now = xbmc.getInfoLabel('Skin.String(aeon.livetv.group)')
            ids = [str(group['channelgroupid']) for group in groups]
            picked = xbmcgui.Dialog().select(xbmc.getInfoLabel('$LOCALIZE[31913]') or 'Channel group', names, preselect=ids.index(now) if now in ids else -1)
            if picked >= 0:
                xbmc.executebuiltin('Skin.SetString(aeon.livetv.group,%s)' % ids[picked])
                xbmc.executebuiltin('Skin.SetString(aeon.livetv.groupname,%s)' % names[picked].replace(',', ' '))
    elif argv[0] == 'sortshow':                        # 0.3.121: the Sort and show only panel (skin dialog 1179)
        from resources.lib import sortshow
        sortshow.run(argv[1:])
    elif argv[0] == 'kbset' and len(argv) >= 2:        # 0.3.120: a suggestion of the Fused Glass style keyboard
        from resources.lib import round3
        round3.kbset(argv[1])
    elif argv[0] == 'setsub' and len(argv) >= 2:       # 0.3.118: a subtitle card in the OSD subtitle panel
        from resources.lib import round3
        round3.setsub(argv[1])
    elif argv[0] == 'review':
        # the review focused on the information page (list 9303): author and full text
        import xbmc
        import xbmcgui
        body = xbmc.getInfoLabel('Container(9303).ListItem.Plot')
        if body:
            xbmcgui.Dialog().textviewer(xbmc.getInfoLabel('Container(9303).ListItem.Label'), body)


if __name__ == '__main__':
    main(sys.argv[1:])
