# -*- coding: utf-8 -*-
"""Where a palette applies (skin 0.40.4): the menus and the library views (''), the menus only ('menus') or the library
views only ('library'). Each is its own colour file of the skin: "Nord.xml", "Nord (menus).xml", "Nord (library).xml"
(made by the skin's _src/pal_scope.py). The Aeon palette (SKINDEFAULT) has no variants."""

DEFAULT = 'SKINDEFAULT'
SCOPES = ('', 'menus', 'library')
SUFFIX = {'menus': ' (menus)', 'library': ' (library)'}


def split(value):
    """Kodi's lookandfeel.skincolors value (with or without .xml) -> (palette, scope).
    'Nord (menus).xml' -> ('Nord', 'menus'); 'Nord' -> ('Nord', ''); '' / 'defaults' -> (SKINDEFAULT, '')."""
    value = (value or '').strip()
    if value.lower().endswith('.xml'):
        value = value[:-4]
    if not value or value.lower() in ('defaults', 'skindefault'):
        return DEFAULT, ''
    for scope, suffix in SUFFIX.items():
        if value.endswith(suffix):
            return value[:-len(suffix)], scope
    return value, ''


def file_for(palette, scope):
    """(palette, scope) -> the colour file's name without .xml (the Aeon palette is always SKINDEFAULT)."""
    if not palette or palette == DEFAULT:
        return DEFAULT
    return palette + SUFFIX.get(scope, '')


def is_variant(name):
    """True for the colour files that only exist as a scope of another palette (left out of the picker's list)."""
    return split(name)[1] != ''
