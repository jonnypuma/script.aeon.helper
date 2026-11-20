# -*- coding: utf-8 -*-
"""Skin settings > Information > Ratings shown in / Media info shown in (0.3.113, skin 0.56.52):
RunScript(script.aeon.helper,placepick,rate|chip) opens a multi-select of the places (resources/lib/places.py);
OK sets their switches and Skin.String(aeon.<kind>.places)."""
import xbmc
import xbmcaddon
import xbmcgui

from resources.lib import places


def pick(kind):
    if kind not in places.KINDS:
        return
    skin = xbmcaddon.Addon('skin.aeon.fuse')
    names = [skin.getLocalizedString(sid) for _p, sid in places.places(kind)]
    now = places.shown(kind, lambda f: xbmc.getCondVisibility('Skin.HasSetting(%s)' % f))
    chosen = xbmcgui.Dialog().multiselect(skin.getLocalizedString(places.KINDS[kind]), names, preselect=now)
    if chosen is None:
        return
    for call in places.builtins(kind, chosen):
        xbmc.executebuiltin(call)
    xbmc.executebuiltin('Skin.SetString(aeon.%s.places,%s)' % (kind, places.summary(kind, chosen)))
