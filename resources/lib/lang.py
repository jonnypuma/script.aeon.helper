# -*- coding: utf-8 -*-
"""The helper's own texts: resources/language/resource.language.<lang>/strings.po, ids 32000+.

L(ident) is the text in Kodi's language (Kodi falls back to en_gb for a missing id). Outside Kodi (the unit tests)
there is no xbmcaddon: L() then returns the English text kept here, the same as en_gb."""

ENGLISH = {
    32000: 'Refresh information',
    32001: 'Update library',
    32002: 'Clean library',
    32003: 'Take screenshot',
    32004: 'Refreshing %s',
    32005: 'Reading the information',
    32006: 'Episode %d of %d',
    32007: 'Refresh failed',
    32008: 'Done',
    32009: 'Information refreshed',
    32010: 'Refresh the information of its episodes too?',
    32011: 'Library',
    32012: 'Video library',
    32013: 'Music library',
    32014: 'Remove the entries of the video library whose files are gone?',
    32015: 'Remove the entries of the music library whose files are gone?',
    32016: 'Updating...',
    32017: 'Daily',
    32018: 'Weekly',
    32019: 'Every 2 weeks',
    32020: 'Monthly',
    32021: 'Home menu',
    32022: 'All %d positions are in use: empty one in Skin settings > Home menu.',
    32023: 'Menu theme',
    32024: 'Kodi restarts to give every menu the new look.',
    32025: 'Later',
    32026: 'Restart',
}

try:
    import xbmcaddon
    _ADDON = xbmcaddon.Addon('script.aeon.helper')
except Exception:          # not inside Kodi
    _ADDON = None


def L(ident):
    if _ADDON is not None:
        try:
            text = _ADDON.getLocalizedString(ident)
        except Exception:
            text = ''
        if text:
            return text
    return ENGLISH.get(ident, '')
