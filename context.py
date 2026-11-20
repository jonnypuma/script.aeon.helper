# -*- coding: utf-8 -*-
"""Context menu items of the Aeon Fuse skin (addon.xml, kodi.context.item). Order and on / off: Skin settings >
Context menu (resources/lib/ctxmenu.py):
  refresh  Refresh information of a film, show, episode or music video, without opening its information page
  update   Update library (video or music, by where the menu was opened)
  clean    Clean library (asks first)
  shot     Take screenshot (on by default)"""
import json
import sys

import xbmc
import xbmcgui

from resources.lib import ctxmenu
from resources.lib.lang import L


def rpc(method, params):
    reply = xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}))
    return json.loads(reply)


def item_type():
    """(DBType, DBID, title) of the item the menu was opened on."""
    item = getattr(sys, 'listitem', None)
    dbtype, dbid, title = '', '', ''
    if item is not None:
        try:
            tag = item.getVideoInfoTag()
            dbtype, dbid, title = tag.getMediaType(), str(tag.getDbId()), tag.getTitle() or item.getLabel()
        except Exception:  # noqa: BLE001 - not a video item
            title = item.getLabel()
    if not dbtype:
        dbtype = xbmc.getInfoLabel('ListItem.DBType')
        dbid = xbmc.getInfoLabel('ListItem.DBID')
        title = title or xbmc.getInfoLabel('ListItem.Label')
    return dbtype, dbid, title


class LibraryWatch(xbmc.Monitor):
    """Collects the video library's OnUpdate notifications: (type, id) of every item Kodi wrote back."""

    def __init__(self):
        super().__init__()
        self.events = []

    def onNotification(self, sender, method, data):  # noqa: N802 - Kodi's name
        if method != 'VideoLibrary.OnUpdate':
            return
        try:
            item = (json.loads(data) or {}).get('item') or {}
        except ValueError:
            return
        if item.get('type'):
            self.events.append((item.get('type'), item.get('id')))


def episode_name(episodeid):
    details = rpc('VideoLibrary.GetEpisodeDetails', {'episodeid': episodeid, 'properties': ['season', 'episode', 'title']})
    got = (details.get('result') or {}).get('episodedetails') or {}
    return got.get('season'), got.get('episode'), got.get('title', '')


def refresh():
    """Refresh one library item without its information page. The progress shows as Aeon Fuse's action toast out
    of the clock box (a background progress dialog): Kodi's refresh job runs in the background, and every item it
    writes back (VideoLibrary.OnUpdate) moves the toast on - for a show, episode by episode."""
    import time
    dbtype, dbid, title = item_type()
    call = ctxmenu.refresh_call(dbtype, dbid)
    if not call:
        return
    method, params = call
    total = 0
    if dbtype == 'tvshow':
        params['refreshepisodes'] = xbmcgui.Dialog().yesno(title, L(32010))
        if params['refreshepisodes']:
            reply = rpc('VideoLibrary.GetEpisodes', {'tvshowid': int(dbid)})
            total = len((reply.get('result') or {}).get('episodes') or [])
    watch = LibraryWatch()
    bar = xbmcgui.DialogProgressBG()
    heading = L(32004) % title
    words = {'line': L(32006), 'reading': L(32005)}
    bar.create(heading, ctxmenu.refresh_line(0, total, title=words['reading'], words=words))
    reply = rpc(method, params)
    if reply.get('result') != 'OK':
        bar.close()
        xbmcgui.Dialog().notification(L(32007), title, xbmcgui.NOTIFICATION_ERROR, 4000)
        return
    started = last = time.time()
    seen = 0
    while not watch.abortRequested():
        if len(watch.events) > seen:
            for kind, itemid in watch.events[seen:]:
                if kind == 'episode' and total:
                    done = sum(1 for k, _i in watch.events if k == 'episode')
                    season, episode, name = episode_name(itemid)
                    bar.update(ctxmenu.refresh_progress(done, total), heading,
                               ctxmenu.refresh_line(done, total, season, episode, name, words=words))
            seen = len(watch.events)
            last = time.time()
        now = time.time()
        if ctxmenu.refresh_finished(dbtype, [k for k, _i in watch.events], total, now - last if watch.events else 0, now - started):
            break
        watch.waitForAbort(0.3)
    bar.update(100, heading, L(32008))
    watch.waitForAbort(0.6)
    bar.close()
    xbmcgui.Dialog().notification(L(32009), title, xbmcgui.NOTIFICATION_INFO, 3000)


def which_library():
    """'video' / 'music' from the item and the window; asks on Home when the item does not tell."""
    dbtype = item_type()[0] if getattr(sys, 'listitem', None) is not None else xbmc.getInfoLabel('ListItem.DBType')
    kind = ctxmenu.library_for(dbtype, xbmc.getCondVisibility('Window.IsActive(music)'), xbmc.getCondVisibility('Window.IsActive(videos)'))
    if kind:
        return kind
    got = xbmcgui.Dialog().select(L(32011), [L(32012), L(32013)])
    return ('video', 'music')[got] if got >= 0 else ''


def update():
    kind = which_library()
    if kind:
        import remotelib
        remotelib.run('update', kind)


def clean():
    kind = which_library()
    if not kind:
        return
    if xbmcgui.Dialog().yesno(L(32002), L(32014) if kind == 'video' else L(32015)):
        import remotelib
        remotelib.run('clean', kind)


def screenshot():
    # the context menu closes first (its close animation would be in the picture); Kodi asks for a folder the first
    # time when Settings > System > Logging > Screenshot folder is empty
    xbmc.sleep(700)
    xbmc.executebuiltin('TakeScreenshot')


if __name__ == '__main__':
    # args="shot,4": Kodi may pass them split or as one string; the place only keeps the 16 items apart
    action = sys.argv[1].split(',')[0].strip() if len(sys.argv) > 1 else ''
    {'refresh': refresh, 'update': update, 'clean': clean, 'shot': screenshot}.get(action, lambda: None)()
