# -*- coding: utf-8 -*-
"""Home menu icons (0.26.0): what Skin settings > Home menu > Choose icon offers, without Kodi (tested in tests/).

The choice is kept per menu item key in Skin.String(aeon.icon.<key>) and the skin reads it through the item's icon
property, so it follows the item when positions are swapped. Paths are skin texture paths (relative to media/)."""

SKIN_DIR = 'aeon/icons/'
AF3_DIR = 'icons/af3/'

# the item's own icon, as the skin's Aeon_H_Icon variable picks it
DEFAULTS = {
    'movies': 'film', 'tv': 'tv', 'music': 'music', 'search': 'search', 'system': 'settings', 'livetv': 'tv',
    'power': 'power', 'sets': 'stack', 'pictures': 'sun', 'weather': 'cloud', 'planner': 'clock',
}

# player / navigation glyphs of the skin's own set: no use as a menu icon
NOT_MENU = {'back', 'chevron_down', 'chevron_right', 'check', 'forward', 'next', 'pause', 'play', 'prev', 'rewind',
            'stop', 'shuffle', 'repeat', 'sidebar', 'ppi', 'chapters', 'subtitles', 'audio'}


def default_icon(key, custom_path=''):
    """The icon an item shows when none is picked. A custom item that opens the movie sets shows the stack."""
    if key.startswith('custom'):
        return SKIN_DIR + ('stack.png' if 'movies/sets' in (custom_path or '') else 'star.png')
    return SKIN_DIR + DEFAULTS.get(key, 'star') + '.png'


def pretty(filename):
    """'apple_tv-plus.png' -> 'Apple tv plus'; names that already have capitals are kept as they are."""
    name = filename.rsplit('/', 1)[-1]
    if name.lower().endswith('.png'):
        name = name[:-4]
    name = name.replace('_', ' ').replace('-', ' ').strip()
    if name and name == name.lower():
        name = name[0].upper() + name[1:]
    return name


def choices(skin_files, af3_files):
    """[(label, texture path)]: the skin's own icons first, then the Arctic Fuse 3 set, each sorted by name."""
    out = []
    for name in sorted((f for f in skin_files if f.lower().endswith('.png')), key=str.lower):
        if name[:-4] not in NOT_MENU:
            out.append((pretty(name), SKIN_DIR + name))
    for name in sorted((f for f in af3_files if f.lower().endswith('.png') and not f.startswith('_')), key=str.lower):
        out.append((pretty(name), AF3_DIR + name))
    return out


def preselect(entries, current):
    """Index to open the picker on: the picked icon, else the first entry (the item's own icon, 'Default')."""
    if current:
        for i, (_label, path) in enumerate(entries):
            if path == current:
                return i
    return 0
