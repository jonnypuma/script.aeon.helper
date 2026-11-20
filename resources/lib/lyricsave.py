# -*- coding: utf-8 -*-
"""Skin settings > Player > "Save lyrics next to the song" (0.3.76): CU LRC Lyrics (script.cu.lrclyrics) saves the lyrics
it finds next to the song file when its settings save_lyrics2_lrc / save_lyrics2_txt are on. The skin row shows
Skin.HasSetting(aeon.lyrics.save); this keeps that in step with the lyrics add-on's own settings."""
import xbmc
import xbmcaddon

LYRICS = 'script.cu.lrclyrics'
KEYS = ('save_lyrics2_lrc', 'save_lyrics2_txt')


def _addon():
    try:
        return xbmcaddon.Addon(LYRICS)
    except Exception:            # not installed or switched off
        return None


def current():
    """True / False as the lyrics add-on has it, None when it is not there."""
    addon = _addon()
    if addon is None:
        return None
    try:
        return any(addon.getSettingBool(key) for key in KEYS)
    except Exception:
        return None


def show(on):
    xbmc.executebuiltin('Skin.SetBool(aeon.lyrics.save)' if on else 'Skin.Reset(aeon.lyrics.save)')


def toggle():
    """The row: switch saving next to the song on or off in the lyrics add-on, and the row with it."""
    addon = _addon()
    if addon is None:
        show(False)
        xbmc.executebuiltin('Notification(CU LRC Lyrics,$LOCALIZE[10005],4000)')     # "Not available"
        return
    on = not current()
    for key in KEYS:
        addon.setSettingBool(key, on)
    show(on)


def sync():
    """At start-up: the row as the lyrics add-on has it (it may have been changed in its own settings)."""
    on = current()
    if bool(on) != bool(xbmc.getCondVisibility('Skin.HasSetting(aeon.lyrics.save)')):
        show(bool(on))
