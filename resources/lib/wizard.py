# -*- coding: utf-8 -*-
"""Setup wizard of Aeon Fuse (dialog 1173): what Finish still has to change.

Steps 4-9 of the wizard set their skin settings at once. Theme and palette wait for Finish, because Kodi shows them
only by loading the skin again, and a skin reload leaves skin settings misread until Kodi restarts (Kodi numbers the
settings again on a reload). So Finish changes both in one go and restarts Kodi where it can."""

DEFAULT = 'SKINDEFAULT'


def plan(theme, glass_now, palette, palette_now):
    """theme: 'aeon' | 'glass' | '' (wizard choice), glass_now: the Glass theme is on, palette: wizard choice (a colors
    file name or SKINDEFAULT), palette_now: Kodi's lookandfeel.skincolors (with or without .xml).
    Returns the changes in order: ('vglass', bool), ('palette', name), ('theme', 'Aeon' | 'Glass')."""
    steps = []
    want_glass = glass_now if theme not in ('aeon', 'glass') else theme == 'glass'
    now = (palette_now or DEFAULT)
    if now.lower().endswith('.xml'):
        now = now[:-4]
    if want_glass != glass_now:
        steps.append(('vglass', want_glass))
    # palettes belong to the Aeon look: remember the choice first (the helper service puts it back after a theme change)
    if not want_glass and palette and palette != now:
        steps.append(('palette', palette))
    if want_glass != glass_now:
        steps.append(('theme', 'Glass' if want_glass else 'Aeon'))
    return steps


def palette_name(value):
    """Kodi's lookandfeel.skincolors value -> the wizard's palette name ('Nord.xml' -> 'Nord', '' -> SKINDEFAULT)."""
    value = (value or '').strip()
    if value.lower().endswith('.xml'):
        value = value[:-4]
    if not value or value.lower() in ('defaults', 'skindefault'):
        return DEFAULT
    return value


def palette_index(name, names):
    """Place of a palette in the wizard's list: SKINDEFAULT first, then the colors files sorted (as wizgen.py writes
    them). Unknown names give 0."""
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
