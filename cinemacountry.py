# -*- coding: utf-8 -*-
"""Skin settings > Spotlight & widgets > In cinemas now: films from (0.3.97, skin 0.56.20).

RunScript(script.aeon.helper,cinemacountry) opens a list: Everywhere, United States, then United States with one more
country. The choice goes to Skin.String(aeon.cinema.country) (the code, read by plugin.py for In cinemas now) and
Skin.String(aeon.cinema.countryname) (what the settings row shows). Country names are shown as they are."""
import xbmc
import xbmcaddon
import xbmcgui

from resources.lib import online

US = 'United States'


def entries(everywhere):
    """[(code, label)]: Everywhere, the United States alone, the United States with each other country."""
    return [('', everywhere), ('US', US)] + [(code, '%s · %s' % (US, name)) for name, code in online.CINEMA_COUNTRIES]


def pick():
    skin = xbmcaddon.Addon('skin.aeon.fuse')
    rows = entries(skin.getLocalizedString(32620))
    now = xbmc.getInfoLabel('Skin.String(aeon.cinema.country)').strip().upper()
    codes = [code for code, _ in rows]
    chosen = xbmcgui.Dialog().select(skin.getLocalizedString(32619), [label for _, label in rows],
                                     preselect=codes.index(now) if now in codes else 0)
    if chosen < 0:
        return
    code, label = rows[chosen]
    if code:
        xbmc.executebuiltin('Skin.SetString(aeon.cinema.country,%s)' % code)
        xbmc.executebuiltin('Skin.SetString(aeon.cinema.countryname,%s)' % label)
    else:
        xbmc.executebuiltin('Skin.Reset(aeon.cinema.country)')
        xbmc.executebuiltin('Skin.Reset(aeon.cinema.countryname)')
