# -*- coding: utf-8 -*-
"""Trailer of the focused library item: the file next to it first, the address the library holds as the fallback.

RunScript(script.aeon.helper,trailer,probe)  information page: put the trailer path in Window(Home) aeon.trailer
RunScript(script.aeon.helper,trailer,flix)   Flix view: play it behind the page (the skin's timer asks for it)
RunScript(script.aeon.helper,trailer,play,<path>)  information page Trailer button: close the page, play full screen"""
import xbmc
import xbmcgui
import xbmcvfs

from resources.lib import trailers


def label(name):
    return xbmc.getInfoLabel('ListItem.%s' % name)


def find():
    kind = label('DBType')
    if kind not in ('movie', 'tvshow', 'season', 'episode'):
        return label('Trailer')
    folder = label('Path')
    base = ''
    if kind in ('movie', 'episode'):
        name = label('FileNameAndPath').replace('\\', '/').rsplit('/', 1)[-1]
        base = trailers.stem(name)
    local = ''
    if folder and not folder.startswith(('videodb://', 'plugin://')):
        try:
            _folders, files = xbmcvfs.listdir(folder)
        except Exception:                 # share asleep or gone: use the library's address
            files = []
        picked = trailers.pick(files, kind, base, label('Season'))
        if picked:
            local = folder + ('' if folder.endswith(('/', '\\')) else '/') + picked
    return local or label('Trailer')


TR_PROPS = ('aeon.tr.now', 'aeon.tr.kind', 'aeon.tr.title', 'aeon.tr.logo', 'aeon.tr.poster')


def whose():
    """The show or film the information page is about (0.39.10): kind (tvshow / movie), name, clearlogo, poster. The
    trailer itself is only a file ("tvshow-trailer.mkv") or a YouTube address, so the player overlays knew nothing."""
    kind = label('DBType')
    if kind in ('tvshow', 'season', 'episode'):
        name = label('TVShowTitle') or label('Title')
        logo = label('Art(tvshow.clearlogo)') or label('Art(clearlogo)')
        poster = label('Art(tvshow.poster)') or label('Art(poster)')
        return 'tvshow', name, logo, poster
    return ('movie' if kind == 'movie' else ''), label('Title'), label('Art(clearlogo)'), label('Art(poster)')


def play(path):
    """The information page's Trailer button. Kodi's own trailer button closes the page before it plays; the skin's
    PlayMedia left it open, and a YouTube trailer then started behind it: when the video began, the busy dialog was the
    top dialog, so Kodi did not close the page while switching to full screen. Close it first, play, and once the
    video runs bring full-screen video to the front if it is not there.
    The overlays (Video OSD, seek bar, information screen) show the show / film the trailer belongs to while that very
    file plays: Window(Home) aeon.tr.now = the playing file, aeon.tr.kind / title / logo / poster."""
    if not path:
        return
    home = xbmcgui.Window(10000)
    kind, name, logo, poster = whose()                  # read while the page (its item) is still open
    for prop in TR_PROPS:
        home.clearProperty(prop)
    before = xbmc.getInfoLabel('Player.FilenameAndPath') if xbmc.getCondVisibility('Player.HasVideo') else ''
    xbmc.executebuiltin('Dialog.Close(movieinformation,true)', True)
    xbmc.executebuiltin('PlayMedia("%s")' % path.replace('"', '\\"'))
    monitor = xbmc.Monitor()
    now = ''
    for _ in range(240):                                # a YouTube trailer can take a minute to resolve
        if monitor.waitForAbort(0.5):
            return
        if xbmc.getCondVisibility('Player.HasVideo'):
            now = xbmc.getInfoLabel('Player.FilenameAndPath')
            if now and now != before:                   # the trailer, not the video that played before it
                break
    else:
        return
    home.setProperty('aeon.tr.kind', kind)
    home.setProperty('aeon.tr.title', name)
    home.setProperty('aeon.tr.logo', logo)
    home.setProperty('aeon.tr.poster', poster)
    home.setProperty('aeon.tr.now', now)
    monitor.waitForAbort(1.0)
    # an information page the user opened meanwhile stays: the video waits under it
    if xbmc.getCondVisibility('Player.HasVideo + !Window.IsActive(fullscreenvideo) + !Window.IsVisible(movieinformation)'):
        xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')


def main(mode, arg=''):
    home = xbmcgui.Window(10000)
    if mode == 'play':
        play(arg)
        return
    path = find()
    if mode == 'probe':
        home.setProperty('aeon.trailer', path)
    elif mode == 'flix' and path and not xbmc.Player().isPlaying():
        if home.getProperty('aeon.flixtrailer'):          # still wanted: the selection has not moved on meanwhile
            xbmc.executebuiltin('PlayMedia("%s",1)' % path)
