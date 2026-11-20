# -*- coding: utf-8 -*-
"""Skin style (skin 0.56.27, helper 0.3.103; no Kodi imports): in Fused Glass the row Skin style (aeon.fgmenu: '' Dark,
glass = Clear, frost = Frost) also sets the library's glass (aeon.fgmat), which library views, Home panels, the Home bar,
the player, Planner and the screensaver read. The Library view theme row is gone; this keeps the two in step at start
(an older setting, Raised, or a choice made in the setup wizard)."""

GLASS = {'glass': 'clear', 'frost': 'frost'}


def library_glass(style):
    """the aeon.fgmat value that belongs to a Skin style ('' = Dark)"""
    return GLASS.get((style or '').strip().lower(), '')


def builtin(style, current):
    """the Skin.SetString / Skin.Reset call that puts aeon.fgmat in step, or None when it already is"""
    want = library_glass(style)
    if (current or '') == want:
        return None
    return 'Skin.SetString(aeon.fgmat,%s)' % want if want else 'Skin.Reset(aeon.fgmat)'


# 0.3.105 (skin 0.56.29): Fused Glass, the System-screen menus, is the fourth style (aeon.fgmenu = system); its library
# glass is Dark. OK on the row steps Dark -> Clear -> Frost -> Fused Glass -> Dark.
ORDER = ['', 'glass', 'frost', 'system']


def next_style(cur):
    cur = (cur or '').strip().lower()
    cur = '' if cur == 'dark' else cur
    return ORDER[(ORDER.index(cur) + 1) % len(ORDER)] if cur in ORDER else ''


def needs_restart(old, new):
    """going to or from Fused Glass changes button textures that load with the skin"""
    return (old == 'system') != (new == 'system')
