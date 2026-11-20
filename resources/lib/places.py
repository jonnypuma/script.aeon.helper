# -*- coding: utf-8 -*-
"""Skin settings > Information > Ratings shown in / Media info shown in (0.3.113, skin 0.56.52; no Kodi imports): where
the ratings and the media info chips are drawn. Every place is on by default; turning one off sets
Skin.HasSetting(aeon.<kind>off.<place>), which the skin ANDs onto the ratings / chip blocks of that place.
The row's value is Skin.String(aeon.<kind>.places) ("5 / 6")."""

# place key, skin string id of its name
PLACES = [('lib', 32753), ('info', 32754), ('widgets', 32755), ('spot', 32756), ('player', 32757), ('ss', 32758),
          ('pvr', 32759)]
# kind -> skin string id of the modal's heading (the row's name)
KINDS = {'rate': 32751, 'chip': 32752}
# the places that have that kind (the screensaver shows no ratings, Live TV no chips)
NOT_IN = {'rate': ('ss',), 'chip': ('pvr',)}


def places(kind):
    return [(p, s) for p, s in PLACES if p not in NOT_IN.get(kind, ())]


def flag(kind, place):
    return 'aeon.%soff.%s' % (kind, place)


def shown(kind, has_setting):
    """indices of the places that show `kind` now. has_setting(name) -> bool (Skin.HasSetting)."""
    return [i for i, (p, _s) in enumerate(places(kind)) if not has_setting(flag(kind, p))]


def builtins(kind, selected):
    """the Skin.SetBool / Skin.Reset calls that make exactly `selected` (indices) the places that show `kind`"""
    on = set(selected)
    return [('Skin.Reset(%s)' if i in on else 'Skin.SetBool(%s)') % flag(kind, p) for i, (p, _s) in enumerate(places(kind))]


def summary(kind, selected):
    return '%d / %d' % (len(set(selected)), len(places(kind)))
