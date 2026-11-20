# -*- coding: utf-8 -*-
"""Skin settings > Details > Media info chips (skin 0.56.22, no Kodi imports): which chips the information page, Home
and the library panels show. Chips that are on by default have a hide switch (aeon.hide.<key>; res / hdr / audio /
aspect are the switches Details already had), the sidecar chips are off by default (aeon.chip.<key>)."""

# key, skin string id of its name, the switch, True = the switch hides it (on by default)
CHIPS = [('res', 32647, 'aeon.hide.res', True), ('aspect', 32648, 'aeon.hide.aspect', True),
         ('hdr', 32649, 'aeon.hide.hdr', True), ('dvp', 32650, 'aeon.hide.dvp', True),
         ('audio', 32651, 'aeon.hide.audio', True), ('channels', 32652, 'aeon.hide.channels', True),
         ('source', 32653, 'aeon.hide.source', True),
         # 0.3.102 (skin 0.56.26): the sidecar's video source, video codec and edition (Version) on their own
         ('vsource', 32665, 'aeon.chip.vsource', False), ('vcodec', 32666, 'aeon.chip.vcodec', False),
         ('edition', 32667, 'aeon.chip.edition', False), ('container', 32654, 'aeon.chip.container', False),
         ('bitrate', 32655, 'aeon.chip.bitrate', False), ('size', 32656, 'aeon.chip.size', False),
         ('subs', 32657, 'aeon.chip.subs', False), ('chapters', 32658, 'aeon.chip.chapters', False),
         ('commentary', 32659, 'aeon.chip.commentary', False), ('3d', 32660, 'aeon.chip.3d', False)]


def shown(has_setting):
    """Indices of the chips that are on now. has_setting(name) -> bool (Skin.HasSetting)."""
    return [i for i, (_k, _s, flag, hides) in enumerate(CHIPS) if has_setting(flag) != hides]


def builtins(selected):
    """The Skin.SetBool / Skin.Reset calls that make exactly `selected` (indices) the chips that are on."""
    out = []
    chosen = set(selected)
    for i, (_k, _s, flag, hides) in enumerate(CHIPS):
        on = i in chosen
        out.append(('Skin.SetBool(%s)' if on != hides else 'Skin.Reset(%s)') % flag)
    return out


def summary(selected):
    return '%d / %d' % (len(set(selected)), len(CHIPS))
