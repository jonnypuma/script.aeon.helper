# -*- coding: utf-8 -*-
"""Setup wizard of Aeon Fuse (dialog 1173, skin 0.56.40): what Finish still has to change, and the defaults.

The wizard's rows change their skin settings at once. Four things wait for Finish because Kodi shows them only by
loading the skin again, and a skin reload leaves skin settings misread until Kodi restarts (Kodi numbers the settings
again on a reload): the theme, the Skin style (aeon.menutheme in Aeon / Aeon Glass, aeon.fgmenu in Fused Glass), the
palette (Aeon) and the fonts. Finish changes them in one go and restarts Kodi where it can."""

DEFAULT = 'SKINDEFAULT'
THEMES = ('fused', 'aeon', 'glass')
# Kodi's Theme setting (lookandfeel.skintheme) per wizard theme
KODI_THEME = {'fused': 'Fused Glass', 'glass': 'Glass', 'aeon': 'Aeon'}
FG_STYLES = ('', 'glass', 'frost', 'system')

# "Use the defaults": the look each theme starts from. PLACEHOLDER until the user's own table (2026-11-17: "i will provide
# the defaults for each theme later"): every setting the wizard shows goes back to the skin's own default ('' = an
# empty string, False = a switch off), and Fused Glass takes the Fused Glass style. Only the settings listed here change;
# the rest of Skin settings stays as it is. menutheme / fgmenu / palette are applied at Finish like the wizard's choices.
COMMON = {
    # Look
    'aeon.fgsdlgbg': '', 'aeon.fgshadow': '', 'aeon.fgfocus': '', 'aeon.fganim': '', 'aeon.toastpill': False,
    'aeon.agfocus': '', 'aeon.agblur': '',                                   # 0.3.110 (skin 0.56.44): Aeon Glass
    'aeon.boxaccent': '',
    # Libraries
    'aeon.boxbg': '', 'aeon.vsbwhite': False, 'aeon.strip.perm': False, 'aeon.libpanel.box': False,
    # Home
    'aeon.lowmenu': False, 'aeon.hm.icons': False, 'aeon.hm.underline': False, 'aeon.npplace': '',
    'aeon.vignette': '', 'aeon.vignette.side': False, 'aeon.homegrad': '', 'aeon.fgnpleft': False,     # 0.3.108 (skin 0.56.42)
    # Backgrounds
    'aeon.nobackdrop': False, 'aeon.backdrop.dim': '', 'aeon.vbg': '', 'aeon.fanartlook': '',
}
# 0.3.114 (skin 0.56.53), the user's first defaults (2026-11-19): Aeon and Aeon Glass put the Color backdrop behind
# every library view (aeon.vbg = color) and keep the corner boxes on Colors ('' = the skin's Colors); Fused Glass as before
AEON_LIB = {'aeon.vbg': 'color', 'aeon.boxbg': ''}
DEFAULTS = {
    'fused': dict(COMMON, fgmenu='system'),
    'aeon': dict(COMMON, menutheme='', palette=DEFAULT, **AEON_LIB),
    'glass': dict(COMMON, menutheme='', **AEON_LIB),
}
DEFERRED = ('menutheme', 'fgmenu', 'palette')


def theme_key(label):
    """Skin.CurrentTheme ('Fused Glass', 'Glass', 'Aeon', 'SKINDEFAULT', '') -> 'fused' | 'glass' | 'aeon'"""
    label = (label or '').strip().lower()
    if label.startswith('fused'):
        return 'fused'
    if label.startswith('glass'):
        return 'glass'
    return 'aeon'


def defaults(theme):
    """(builtins for the settings that change at once, {deferred name: value}) for the theme's defaults"""
    table = DEFAULTS.get(theme, DEFAULTS['fused'])
    calls, later = [], {}
    for key in sorted(table):
        value = table[key]
        if key in DEFERRED:
            later[key] = value
        elif value is True:
            calls.append('Skin.SetBool(%s)' % key)
        elif value is False or value == '':
            calls.append('Skin.Reset(%s)' % key)
        else:
            calls.append('Skin.SetString(%s,%s)' % (key, value))
    return calls, later


def _menutheme(value):
    value = (value or '').strip().lower()
    return '' if value in ('', 'bridge', 'aeon') else value


def _fgmenu(value):
    value = (value or '').strip().lower()
    return value if value in FG_STYLES else ''


def plan(want, now):
    """want: the wizard's choices, now: what runs; dicts with theme ('fused' | 'aeon' | 'glass'), menutheme, fgmenu,
    palette (a colors file name or SKINDEFAULT; now: Kodi's lookandfeel.skincolors, with or without .xml).
    Returns the changes in order: ('menutheme', v), ('fgmenu', v), ('palette', name), ('theme', key)."""
    steps = []
    theme = want.get('theme') if want.get('theme') in THEMES else now.get('theme')
    if theme == 'fused':
        if _fgmenu(want.get('fgmenu')) != _fgmenu(now.get('fgmenu')):
            steps.append(('fgmenu', _fgmenu(want.get('fgmenu'))))
    elif theme == 'glass':
        # Aeon Glass has its own menus or Fuse; the Aeon menu styles do not count there
        if (_menutheme(want.get('menutheme')) == 'fused') != (_menutheme(now.get('menutheme')) == 'fused'):
            steps.append(('menutheme', 'fused' if _menutheme(want.get('menutheme')) == 'fused' else ''))
    elif _menutheme(want.get('menutheme')) != _menutheme(now.get('menutheme')):
        steps.append(('menutheme', _menutheme(want.get('menutheme'))))
    # palettes belong to the Aeon look: remember the choice first (the helper service puts it back after a theme change)
    palette = want.get('palette')
    if theme == 'aeon' and palette and palette != palette_name(now.get('palette')):
        steps.append(('palette', palette))
    if theme != now.get('theme'):
        steps.append(('theme', theme))
    return steps


def palette_name(value):
    """Kodi's lookandfeel.skincolors value -> the wizard's palette name ('Nord.xml' -> 'Nord', '' -> SKINDEFAULT)."""
    value = (value or '').strip()
    if value.lower().endswith('.xml'):
        value = value[:-4]
    if not value or value.lower() in ('defaults', 'skindefault'):
        return DEFAULT
    # a palette for the menus / the library only (skin 0.40.4) is still that palette in the wizard's list
    for suffix in (' (menus)', ' (library)'):
        if value.endswith(suffix):
            return value[:-len(suffix)]
    return value


def palette_index(name, names):
    """Place of a palette in the wizard's list: SKINDEFAULT first, then the colors files sorted. Unknown names give 0."""
    order = [DEFAULT] + sorted(names)
    return order.index(name) if name in order else 0


def menu_switch(positions, hidden, key):
    """Setup wizard > Home menu items: what switching `key` does. positions: the item of every Home menu position
    (1-based list order, 'off' for an empty one), hidden: their hide switches (True = hidden).
    Returns ('show', n) / ('hide', n) for a position that has the item, ('place', n) for the first empty position,
    or ('full', 0) when the item is not on the menu and no position is free."""
    for n, item in enumerate(positions, 1):
        if item == key:
            return ('show', n) if hidden[n - 1] else ('hide', n)
    for n, item in enumerate(positions, 1):
        if item in ('', 'off'):
            return 'place', n
    return 'full', 0


def can_restart(platform):
    """Kodi's RestartApp starts Kodi again only on Linux (CoreELEC / LibreELEC restart it, the kodi launcher script
    loops on its exit code). On Windows it just quits (tested, Kodi 23); Android, iOS, tvOS and macOS: not used."""
    return platform == 'linux'
