# -*- coding: utf-8 -*-
"""Skin settings > Details > Media info chips (0.3.98, skin 0.56.22): RunScript(script.aeon.helper,chippick) opens a
multi-select of the chips (resources/lib/chips.py); OK sets their switches and Skin.String(aeon.chips.shown)."""
import xbmc
import xbmcaddon
import xbmcgui

from resources.lib import chips


def pick():
    skin = xbmcaddon.Addon('skin.aeon.fuse')
    names = [skin.getLocalizedString(sid) for _k, sid, _f, _h in chips.CHIPS]
    now = chips.shown(lambda flag: xbmc.getCondVisibility('Skin.HasSetting(%s)' % flag))
    chosen = xbmcgui.Dialog().multiselect(skin.getLocalizedString(32645), names, preselect=now)
    if chosen is None:
        return
    for call in chips.builtins(chosen):
        xbmc.executebuiltin(call)
    xbmc.executebuiltin('Skin.SetString(aeon.chips.shown,%s)' % chips.summary(chosen))
