# -*- coding: utf-8 -*-
"""RunScript(script.aeon.helper,swap,<position>,<-1|1>) moves a Home menu position up or down.
RunScript(script.aeon.helper,reset) restores the default order.
RunScript(script.aeon.helper,fonts) picks a font family per section of the skin (fontpick.py).

Skin strings cannot be swapped from the skin itself: Kodi expands every $INFO in an action list before the first
action runs, so a temporary copy is stale. Done here, one string at a time."""
import sys
import xbmc
import xbmcgui

DEFAULT = ['movies', 'tv', 'music', 'livetv', 'search', 'system', 'power', 'planner', 'off', 'off', 'off', 'off', 'off']
FIRST_ROW_ID = 9590
COUNT = 13          # 13 positions: the presets of a full menu and still room for the three custom items


def row_id(n):
    """Skin settings > Home menu: the row of position n (1-10: 9590-9599, 11-13: 9613-9615; 9600 is a category)."""
    return FIRST_ROW_ID + n - 1 if n <= 10 else 9602 + n


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
    ('custom1', 'Custom item 1', ''),
    ('custom2', 'Custom item 2', ''),
    ('custom3', 'Custom item 3', ''),
]


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
    opens the sets, or a free one set up for them ('' when all three are taken: the preset is used then)."""
    free = [key for key in customs if key not in used]
    for key in free:
        if 'movies/sets' in xbmc.getInfoLabel('Skin.String(CustomMenu.%s.Path)' % key[-1]):
            return key
    for key in free:
        number = key[-1]
        if not xbmc.getInfoLabel('Skin.String(CustomMenu.%s.Path)' % number):
            label = xbmc.getInfoLabel('$VAR[Aeon_Name_sets]') or 'Movie sets'
            xbmc.executebuiltin('Skin.SetString(CustomMenu.%s.Label,%s)' % (number, label))
            xbmc.executebuiltin('Skin.SetString(CustomMenu.%s.Path,%s)' % (number, SETS_PATH))
            xbmc.executebuiltin('Skin.SetString(CustomMenu.%s.Target,videos)' % number)
            return key
    return ''


def choose(n):
    """Choose type: a preset that is not on the menu yet, a custom item, or nothing. There are three custom items
    behind the scenes (each keeps its own path, spotlight and lists); the first free one is taken."""
    if not 1 <= n <= COUNT:
        return
    current = get(n)
    used = set(get(i) for i in range(1, COUNT + 1) if i != n)
    presets = [it for it in ITEMS if not it[0].startswith('custom') and it[0] not in used]
    customs = [it[0] for it in ITEMS if it[0].startswith('custom')]
    free_custom = current if current.startswith('custom') else next((key for key in customs if key not in used), '')
    text = lambda ident, fallback: xbmc.getInfoLabel('$LOCALIZE[%d]' % ident) or fallback
    keys = [it[0] for it in presets]
    labels = [xbmc.getInfoLabel(it[1]) or it[0] for it in presets]
    keys.append(free_custom or 'nocustom')
    labels.append(text(31909, 'Custom item'))
    keys.append('off')
    labels.append(text(31910, 'Empty position'))
    preselect = keys.index(current) if current in keys else -1
    picked = xbmcgui.Dialog().select(text(31911, 'Type of position') + ' %d' % n, labels, preselect=preselect)
    if picked < 0:
        return
    key = keys[picked]
    if key == 'sets':
        key = sets_item(customs, used) or key
    if key == 'nocustom':
        xbmcgui.Dialog().ok(text(31909, 'Custom item'), text(31912, 'All three custom items are in use. Free one first.'))
        return
    put(n, key)
    set_hidden(n, False)
    old = old_hide_setting(key)
    if old:
        xbmc.executebuiltin('Skin.Reset(HideMenu.%s)' % old)


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
    custom_path = xbmc.getInfoLabel('Skin.String(CustomMenu.%s.Path)' % key[-1]) if key.startswith('custom') else ''
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
    for n, value in enumerate(DEFAULT, 1):
        put(n, value)
        set_hidden(n, False)


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


def open_wizard():
    """Home (first run) and Skin settings > Setup wizard: publish what the wizard starts from, then open it (dialog
    1173). Done here, in order: the dialog's own onload actions run later than their conditions are read."""
    import json
    import palette
    from resources.lib import wizard
    if xbmc.getSkinDir() != 'skin.aeon.fuse' or xbmc.getCondVisibility('Window.IsVisible(1173)'):
        return
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'Settings.GetSettingValue',
                                                       'params': {'setting': 'lookandfeel.skincolors'}})))
    name = wizard.palette_name((reply.get('result') or {}).get('value', ''))
    home = xbmcgui.Window(10000)
    home.setProperty('aeon.wiz.theme', 'glass' if xbmc.getCondVisibility('Skin.HasSetting(aeon.vglass)') else 'aeon')
    home.setProperty('aeon.wiz.palette', name)
    home.setProperty('aeon.wiz.pal0', name)
    home.setProperty('aeon.wiz.palidx', str(wizard.palette_index(name, palette.names())))
    for prop in ('pw', 'pk', 'pk2', 'pa'):          # the wizard's own colours: the skin's until a palette is picked
        home.clearProperty('aeon.wiz.%s' % prop)
    home.setProperty('aeon.wiz.step', '1')
    xbmc.executebuiltin('ActivateWindow(1173)')


def finish_wizard():
    """Setup wizard (dialog 1173) > Finish: mark it done, then apply the theme and palette it chose and restart Kodi
    (a skin reload alone leaves skin settings misread until the next start)."""
    import json
    from resources.lib import wizard
    home = xbmcgui.Window(10000)
    theme = home.getProperty('aeon.wiz.theme')
    chosen = home.getProperty('aeon.wiz.palette')
    xbmc.executebuiltin('Skin.SetBool(aeon.wizard.done)')
    xbmc.executebuiltin('Dialog.Close(1173)')
    monitor = xbmc.Monitor()
    for _ in range(40):
        if not xbmc.getCondVisibility('Window.IsVisible(1173)') or monitor.waitForAbort(0.05):
            break

    def rpc(method, params):
        return json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})))

    colours = (rpc('Settings.GetSettingValue', {'setting': 'lookandfeel.skincolors'}).get('result') or {}).get('value', '')
    steps = wizard.plan(theme, bool(xbmc.getCondVisibility('Skin.HasSetting(aeon.vglass)')), chosen, colours)
    if not steps:
        return
    for what, value in steps:
        if what == 'vglass':
            # the service follows the theme with this switch; set first, so it has nothing to reload
            xbmc.executebuiltin('Skin.SetBool(aeon.vglass)' if value else 'Skin.Reset(aeon.vglass)')
        elif what == 'palette':
            xbmc.executebuiltin('Skin.SetString(aeon.palette,%s)' % value)
            if not rpc('Settings.SetSettingValue', {'setting': 'lookandfeel.skincolors', 'value': value}).get('result'):
                rpc('Settings.SetSettingValue', {'setting': 'lookandfeel.skincolors', 'value': value + '.xml'})
        elif what == 'theme':
            rpc('Settings.SetSettingValue', {'setting': 'lookandfeel.skintheme', 'value': value})
        monitor.waitForAbort(0.5)
    platform = next((name for name in ('android', 'windows', 'osx', 'linux')
                     if xbmc.getCondVisibility('System.Platform.%s' % name)), '')
    if wizard.can_restart(platform):
        monitor.waitForAbort(1.0)
        xbmc.executebuiltin('RestartApp')


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
    elif argv[0] == 'icon' and len(argv) >= 2 and argv[1].isdigit():
        icon(int(argv[1]))
    elif argv[0] == 'epggroup':
        epg_group()
    elif argv[0] == 'albumview':
        album_view()
    elif argv[0] == 'reset':
        reset()
    elif argv[0] == 'fonts':
        import fontpick
        fontpick.pick()
    elif argv[0] == 'palette':
        import palette
        palette.pick()
    elif argv[0] == 'ctx' and len(argv) >= 3:
        ctx(argv[1:])
    elif argv[0] == 'rescan':
        # after the add-on's files were replaced by hand: make Kodi read addon.xml again
        import xbmc
        xbmc.executebuiltin('UpdateLocalAddons')
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
        else:
            finish_wizard()
    elif argv[0] == 'arr':
        import arrfeed
        arrfeed.main()
    elif argv[0] == 'search' and len(argv) >= 2:
        import searchhist
        searchhist.run(argv[1])
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
            request = {'jsonrpc': '2.0', 'id': 1, 'method': 'Settings.SetSettingValue',
                       'params': {'setting': 'lookandfeel.skintheme', 'value': names[wanted]}}
            xbmc.executeJSONRPC(json.dumps(request))
    elif argv[0] == 'focusstrip' and len(argv) >= 2 and argv[1].isdigit():
        # Home: Down on Movies / TV / Music while the strip under the menu is still loading (its path waits for the
        # submenu list, then it loads its own titles): focus it as soon as it has items, unless the menu moved on
        import xbmc
        strip = int(argv[1])
        section = xbmc.getInfoLabel('Container(9000).ListItem.Label2')
        monitor = xbmc.Monitor()
        for _ in range(50):
            if monitor.waitForAbort(0.1):
                return
            if not xbmc.getCondVisibility('Control.HasFocus(9000)') or xbmc.getInfoLabel('Container(9000).ListItem.Label2') != section:
                return
            if xbmc.getCondVisibility('Integer.IsGreater(Container(%d).NumItems,0)' % strip):
                xbmc.executebuiltin('SetFocus(%d)' % strip)
                return
    elif argv[0] == 'menutheme':
        # Skin settings > Appearance > Menu theme: the menus choose their look while the skin loads (button textures cannot
        # follow a setting live), so a change needs the skin loaded again. A reload leaves skin settings misread until the
        # next start, so on boxes that restart cleanly (CoreELEC / Linux) Kodi restarts instead, when the user agrees.
        import xbmc
        import xbmcgui
        from resources.lib import wizard
        fused = xbmc.getInfoLabel('Skin.String(aeon.menutheme)') == 'fused'
        want = (argv[1] == 'fused') if len(argv) >= 2 else not fused
        if want == fused:
            return
        xbmc.executebuiltin('Skin.SetString(aeon.menutheme,fused)' if want else 'Skin.Reset(aeon.menutheme)')
        xbmc.sleep(300)
        platform = next((name for name in ('android', 'windows', 'osx', 'linux')
                         if xbmc.getCondVisibility('System.Platform.%s' % name)), '')
        if wizard.can_restart(platform):
            from resources.lib.lang import L
            if xbmcgui.Dialog().yesno(L(32023), L(32024), nolabel=L(32025), yeslabel=L(32026)):
                xbmc.executebuiltin('RestartApp')
        else:
            xbmc.executebuiltin('ReloadSkin()')
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
    elif argv[0] == 'planner' and len(argv) >= 2:
        import plannerwin
        plannerwin.main(argv[1])
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
    elif argv[0] == 'review':
        # the review focused on the information page (list 9303): author and full text
        import xbmc
        import xbmcgui
        body = xbmc.getInfoLabel('Container(9303).ListItem.Plot')
        if body:
            xbmcgui.Dialog().textviewer(xbmc.getInfoLabel('Container(9303).ListItem.Label'), body)


if __name__ == '__main__':
    main(sys.argv[1:])
