import datetime
import json
import os
import re
import sys
import threading
import time

import xbmc
import xbmcgui
import xbmcvfs

import arrfeed
import artguard
import artistcache
import blurcache
import chapterwin
import logocache
import menufile
import nextaired
import searchhist
import videocache
from resources.lib import backdrops, boxart, cinema, dvprofile, planner
from resources.lib.counts import album_counts, album_tracks, fetch_counts
from resources.lib.episodes import fetch_epmark
from resources.lib.headline import bold_last
from resources.lib.ratings import NAMES, fetch_ratings
from resources.lib.themes import find_theme
from resources.lib.uptime import short as short_uptime

PREFIX = 'aeon.count.'
RATING_PREFIX = 'aeon.r.'
# containers the skin reads by number (Home spotlight / strips, set and version panes)
CONTAINERS = (9301, 9302, 9421, 9422, 5221, 5241, 5224, 5244, 5104, 5101, 9441)
COUNT_INTERVAL = 600
POLL = 0.3


def rpc(method, params):
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return json.loads(xbmc.executeJSONRPC(request))


def publish():
    home = xbmcgui.Window(10000)
    for name, value in fetch_counts(rpc).items():
        home.setProperty(PREFIX + name, str(value))


def player_key():
    """(media type, library id) of the video playing, ('', '') when none: the player's ratings follow it."""
    dbid = xbmc.getInfoLabel('VideoPlayer.DBID')
    if not dbid or not xbmc.getCondVisibility('Player.HasVideo'):
        return ('', '')
    try:
        kind = xbmc.Player().getVideoInfoTag().getMediaType()
    except RuntimeError:
        return ('', '')
    return (kind or '', dbid)


def publish_ratings(ratings, container=None):
    home = xbmcgui.Window(10000)
    prefix = RATING_PREFIX if container is None else '%s%s.' % (RATING_PREFIX, container)
    for name in NAMES:
        home.setProperty(prefix + name, ratings.get(name, ''))


def sync_theme(state):
    """Kodi's own Theme setting (Settings > Interface > Skin > Theme: Aeon / Glass / Fused Glass, "Skin default" = Aeon)
    decides which look the skin draws; the skin reads it as Skin.HasSetting(aeon.vglass) and Skin.HasSetting(aeon.fglass)."""
    if xbmc.getSkinDir() != 'skin.aeon.fuse':
        return
    theme = xbmc.getInfoLabel('Skin.CurrentTheme')
    if not theme or theme == state.get('theme'):
        return
    state['theme'] = theme
    # Fused Glass is built on Glass: it sets both aeon.vglass and aeon.fglass, and draws its own variant wherever it has one
    fused = theme.lower().startswith('fused')
    glass = theme.lower().startswith('glass') or fused
    if fused:
        # its own colours (colors/Fused Glass.xml); Kodi picks them on a theme change, set them if it did not
        now = (rpc('Settings.GetSettingValue', {'setting': 'lookandfeel.skincolors'}).get('result') or {}).get('value', '')
        if os.path.splitext(now)[0] != 'Fused Glass':
            rpc('Settings.SetSettingValue', {'setting': 'lookandfeel.skincolors', 'value': 'Fused Glass.xml'})
    if not glass:
        # palettes belong to the Aeon look; Kodi resets the colours on a theme change, so put the chosen one back
        wanted = xbmc.getInfoLabel('Skin.String(aeon.palette)')
        now = (rpc('Settings.GetSettingValue', {'setting': 'lookandfeel.skincolors'}).get('result') or {}).get('value', '')
        if wanted and wanted != 'SKINDEFAULT' and os.path.splitext(now)[0] != wanted:
            rpc('Settings.SetSettingValue', {'setting': 'lookandfeel.skincolors', 'value': wanted})
    changed = False
    if fused != bool(xbmc.getCondVisibility('Skin.HasSetting(aeon.fglass)')):
        xbmc.executebuiltin('Skin.SetBool(aeon.fglass)' if fused else 'Skin.Reset(aeon.fglass)')
        changed = True
    if glass != bool(xbmc.getCondVisibility('Skin.HasSetting(aeon.vglass)')):
        xbmc.executebuiltin('Skin.SetBool(aeon.vglass)' if glass else 'Skin.Reset(aeon.vglass)')
        changed = True
    if changed:
        # parts of the skin choose their Glass / Aeon variant while it loads: load it again with the new value
        xbmc.sleep(500)
        xbmc.executebuiltin('ReloadSkin()')


def refresh_nextaired(monitor, last_played):
    """Planner: read the upcoming episodes again when the kept list is due (the Planner's Update option, every two weeks
    by default; a partly failed read is tried again after six hours). Never during playback: a due read waits until
    playback (playing or paused) has been over for three minutes and nobody has pressed a key for three minutes
    (planner.quiet_enough), and stops if something starts playing. Never two at a time."""
    if xbmc.getSkinDir() != 'skin.aeon.fuse' or xbmc.Player().isPlaying():
        return
    if not planner.quiet_enough(time.time(), last_played, xbmc.getCondVisibility('System.IdleTime(%d)' % planner.QUIET)):
        return
    if not nextaired.stale():
        return
    if any(thread.name == 'aeon-nextaired' for thread in threading.enumerate()):
        return
    threading.Thread(target=nextaired.build, args=(monitor,), name='aeon-nextaired').start()


def refresh_videos(monitor, force=False):
    """Online lists: (re)build the file of library titles in the background; the lists are matched against it."""
    def work():
        if force:
            videocache.drop()
        if videocache.load() is None:
            videocache.build(monitor)
    threading.Thread(target=work, name='aeon-videos').start()


def refresh_artists(monitor, force=False):
    """Similar artists row: (re)build the artist-genre file in the background; the artist page reads it."""
    def work():
        if force:
            artistcache.drop()
        if artistcache.load() is None:
            artistcache.build(monitor)
    threading.Thread(target=work, name='aeon-artists').start()


ART_GUARD = artguard.Guard()


class Monitor(xbmc.Monitor):
    def onNotification(self, sender, method, data):
        # library art with the wrong shape (a landscape picture as a season poster): checked once Kodi is quiet
        if method == 'VideoLibrary.OnUpdate':
            ART_GUARD.queue(data)

    def onScanFinished(self, library):
        publish()
        if library == 'music':
            refresh_artists(self, force=True)
        if library == 'video':
            refresh_videos(self, force=True)

    def onCleanFinished(self, library):
        publish()


VIEW_OPTIONS = ('ratings', 'mediainfo', 'plot', 'bg', 'strip', 'bgs', 'bio', 'art', 'counts', 'watched', 'trailer')


def publish_view_options(shown):
    """Per-view overrides (skin strings aeon.vo.<content>.<viewmode>.<option>) -> Home properties aeon.vo.<option>.
    Empty = follow the global setting. Only library windows have overrides.
    While the settings strip / View settings dialog is open, 'Container' means the dialog's own list, so the key of the
    view underneath is kept (and published as aeon.vo.base for the dialog to write to)."""
    home = xbmcgui.Window(10000)
    if not xbmc.getCondVisibility('Window.IsActive(videos) | Window.IsActive(music)'):
        base = ''
    elif xbmc.getCondVisibility('Window.IsActive(1160) | Window.IsActive(1166) | System.HasActiveModalDialog'):
        base = shown.get('base', '')
    else:
        content, mode = xbmc.getInfoLabel('Container.Content'), xbmc.getInfoLabel('Container.Viewmode')
        base = 'aeon.vo.%s.%s.' % (content, mode) if content and mode else ''
    if shown.get('base') != base:
        shown['base'] = base
        home.setProperty('aeon.vo.base', base)
    for option in VIEW_OPTIONS:
        value = xbmc.getInfoLabel('Skin.String(%s%s)' % (base, option)) if base else ''
        if shown.get(option) != value:
            shown[option] = value
            home.setProperty('aeon.vo.' + option, value)


SETTLE = 1.0   # seconds the selection must rest before a theme starts


class Themes(object):
    """Plays theme.mp3 from the selected movie / show folder (Skin setting aeon.themesongs, default off).
    Only ever starts when nothing else is playing, only ever stops its own theme."""

    def __init__(self):
        self.player = xbmc.Player()
        self.playing = ''
        self.target = None
        self.since = 0.0
        self.last_path = None

    def ours(self):
        return bool(self.playing) and self.player.isPlaying() and self.player.getPlayingFile() == self.playing

    def stop(self):
        if self.ours():
            self.player.stop()
        self.playing = ''
        xbmcgui.Window(10000).clearProperty('aeon.theme')
        xbmc.executebuiltin('PlayerControl(RepeatOff)')

    def wanted(self):
        if not xbmc.getCondVisibility('Skin.HasSetting(aeon.themesongs) + Window.IsActive(videos)'):
            return ''
        if not xbmc.getCondVisibility('Container.Content(movies) | Container.Content(tvshows)'):
            return ''
        path = xbmc.getInfoLabel('ListItem.Path')
        if path != self.last_path:
            self.last_path = path
            self.theme_file = find_theme(path, xbmcvfs.exists)
        return getattr(self, 'theme_file', '')

    def tick(self):
        want = self.wanted()
        if self.playing and not self.ours():
            # finished, or the user started something else: never fight it
            self.playing = ''
            xbmcgui.Window(10000).clearProperty('aeon.theme')
            xbmc.executebuiltin('PlayerControl(RepeatOff)')
        if want != self.target:
            self.target = want
            self.since = time.time()
        if self.playing and want != self.playing:
            self.stop()
        if want and not self.playing and time.time() - self.since >= SETTLE and not self.player.isPlaying():
            self.player.play(want, windowed=True)
            self.playing = want
            xbmcgui.Window(10000).setProperty('aeon.theme', '1')
            xbmc.executebuiltin('PlayerControl(RepeatOne)')


BOX_DARKEN = 0.62   # the artwork colour is lit for a dark room (L 0.55); white text on a box needs it darker


def box_colour(main):
    """'FFRRGGBB' -> the same hue darkened, or '' when the value is not a colour."""
    main = (main or '').strip()
    if len(main) != 8:
        return ''
    try:
        rgb = [int(main[i:i + 2], 16) for i in (2, 4, 6)]
    except ValueError:
        return ''
    return 'FF%02X%02X%02X' % tuple(int(c * BOX_DARKEN) for c in rgb)


BOX_REST = 0.4      # seconds the selection must rest before its colour is asked for
BOX_PREFIX = 'AeonBox'


class BoxColours(object):
    """KarmaMole's renderer, run inside this service.
    The colours used to be asked for with RunScript(script.karmamole.helper,action=colours,...) for every item the
    selection rested on. Each RunScript starts a new Python interpreter (and loads the image library into it); Kodi
    does not give all of that back, about 2 MB each, so browsing a library made Kodi's memory climb by gigabytes on
    CoreELEC. Here one renderer lives as long as the service and works in a background thread, one picture at a time.
    If KarmaMole's code cannot be loaded (another version), the old RunScript is used."""

    def __init__(self):
        self.glow = None        # kmhelper.glow once loaded; False when it cannot be
        self.renderer = None
        self.publisher = None
        self.thread = None

    def _load(self):
        if self.glow is None:
            try:
                import xbmcaddon
                path = xbmcaddon.Addon('script.karmamole.helper').getAddonInfo('path')
                lib = os.path.join(xbmcvfs.translatePath(path), 'resources', 'lib')
                if lib not in sys.path:
                    sys.path.append(lib)
                from kmhelper import glow
                glow.Renderer, glow.Publisher  # noqa: B018 - both must be there
                self.glow = glow
            except Exception as exc:  # noqa: BLE001
                xbmc.log('[script.aeon.helper] KarmaMole renderer not usable in-process (%s): using RunScript' % exc, xbmc.LOGWARNING)
                self.glow = False
        return self.glow

    def request(self, art, soft):
        """Start the colours of this picture; False while the previous one is still being worked on."""
        glow = self._load()
        if not glow:
            xbmc.executebuiltin('RunScript(script.karmamole.helper,action=colours,"image=%s",prefix=%s)' % (art, BOX_PREFIX))
            return True
        if self.thread is not None and self.thread.is_alive():
            return False
        if self.renderer is None:
            self.renderer = glow.Renderer(soft=soft)
            self.publisher = glow.Publisher('Groove.' + BOX_PREFIX, threaded=False)
        else:
            self.renderer.set_soft(soft)
        renderer, publisher = self.renderer, self.publisher

        def work():
            try:
                publisher.publish(art, renderer.render(art))
            except Exception as exc:  # noqa: BLE001
                xbmc.log('[script.aeon.helper] colours of %s failed: %s' % (art, exc), xbmc.LOGWARNING)

        self.thread = threading.Thread(target=work, name='aeon-boxcolours')
        self.thread.daemon = True
        self.thread.start()
        return True


BOX = BoxColours()


def sync_karmamole(state):
    """Artwork colours from the KarmaMole helper (if installed).
    - 'colours': the clock / count / strip boxes of the library views take the colour of the focused item's POSTER
      (album: cover, episode: its thumbnail, see resources/lib/boxart.py), published as aeon.boxcol, unless the skin setting aeon.nopalette is on. The helper's own
      Groove.Color.Main follows the fanart, which gave boxes that did not match the poster on screen, so the poster is
      rendered with KarmaMole's own renderer inside this service (BoxColours) and the answer read from Groove.AeonBox.*.
    - 'softart': only while a backdrop setting actually uses Colors."""
    home = xbmcgui.Window(10000)
    installed = xbmc.getCondVisibility('System.AddonIsEnabled(script.karmamole.helper)')
    boxes = installed and not xbmc.getCondVisibility('Skin.HasSetting(aeon.nopalette)')
    # not under the screensaver: its slides count as the focused item of the library underneath, and every request
    # starts a new Python interpreter (RunScript) that Kodi does not fully give back (about 2 MB each)
    in_library = xbmc.getCondVisibility('[Window.IsActive(videos) | Window.IsActive(music)] + !System.ScreenSaverActive')
    # Backdrop = Colors somewhere: a library view (global, per section or per view) or the screensaver / spotlight
    page = installed and in_library and (
        home.getProperty('aeon.vo.bg') == 'color' or
        (not home.getProperty('aeon.vo.bg') and 'color' in [xbmc.getInfoLabel('Skin.String(aeon.vbg%s)' % x)
                                                           for x in ('', '.movies', '.tv', '.music')]))
    wash = installed and (page or 'color' in [xbmc.getInfoLabel('Skin.String(aeon.%s)' % x) for x in ('ssbg', 'spbg', 'wsbg')])
    want = ','.join(name for name, on in (('colours', boxes or wash), ('softart', wash)) if on)
    if home.getProperty('KarmaMole.Helper.Features') != want:
        home.setProperty('KarmaMole.Helper.Features', want)
    colour = ''
    artcol = soft = ''
    if (boxes or page) and in_library:
        art = ''
        for key in boxart.art_keys(xbmc.getInfoLabel('ListItem.DBType')):
            art = xbmc.getInfoLabel('ListItem.Art(%s)' % key)
            if art:
                break
        now = time.time()
        if art != state.get('art'):
            state['art'] = art
            state['since'] = now
        elif art and art != state.get('asked') and now - state.get('since', now) >= BOX_REST and '"' not in art:
            if BOX.request(art, bool(wash)):
                state['asked'] = art
        if art and home.getProperty('Groove.%s.Art.Source' % BOX_PREFIX) == art:
            main = home.getProperty('Groove.%s.Color.Main' % BOX_PREFIX)
            colour = box_colour(main)
            artcol = main if colour else ''
            soft = home.getProperty('Groove.%s.Art.Soft' % BOX_PREFIX)
        elif art:
            # keep the last values until the new ones arrive: no flash back to the defaults
            colour, artcol, soft = state.get('box', ''), state.get('artcol', ''), state.get('soft', '')
        if not boxes:
            colour = ''
        if not page:
            artcol = soft = ''
    for key, prop, value in (('box', 'aeon.boxcol', colour), ('artcol', 'aeon.artcol', artcol), ('soft', 'aeon.wash', soft)):
        if state.get(key) != value:
            state[key] = value
            home.setProperty(prop, value)


def sync_spot_container(state):
    """Home spotlight with Spotlight background = Colors: the colour picture is KarmaMole's (Groove.Art.Soft), made from
    the item of the list named in Groove.Helper.Container. Nothing named it on Home, so KarmaMole read the focused main
    menu (no artwork), never made a picture, and the spotlight had no colour background at all. Name the spotlight list
    on screen while Home shows it. Over Home, the widget screens (dialog 1157, Widget screens: background = Color) name
    their page list in focus instead. The screensaver sets its own list (9701) and is left alone."""
    home = xbmcgui.Window(10000)
    if xbmc.getCondVisibility('System.ScreenSaverActive'):
        return
    want = ''
    if xbmc.getCondVisibility('Window.IsVisible(1157)'):
        if xbmc.getCondVisibility('String.IsEqual(Skin.String(aeon.wsbg),color)'):
            cid = xbmc.getInfoLabel('System.CurrentControlId')
            if boxart.is_widget_list(cid):
                want = cid
    elif xbmc.getCondVisibility('Window.IsActive(home) + String.IsEqual(Skin.String(aeon.spbg),color)'):
        cid = boxart.spot_list(xbmc.getInfoLabel('Container(9000).ListItem.Label2'))
        if cid and xbmc.getCondVisibility('Integer.IsGreater(Container(%d).NumItems,0)' % cid):
            want = str(cid)
    now = home.getProperty('Groove.Helper.Container')
    if want and now != want:
        home.setProperty('Groove.Helper.Container', want)
    elif not want and now and now == state.get('spot'):
        home.clearProperty('Groove.Helper.Container')
    state['spot'] = want


SPOT_SECTIONS = ('movies', 'tv', 'music', 'custom1', 'custom2', 'custom3')
# custom spotlights (0.3.61): the heading by sort, from the skin's templates 32433-32439 ("Random %s"), %s = item name
CUSTOM_HEAD_IDS = {'random': 32433, 'dateadded': 32434, 'lastplayed': 32435, 'rating': 32436, 'playcount': 32437,
                   'year': 32438, 'title': 32439}


def custom_head(sec):
    """Heading of a custom item's spotlight, like Movies ("Random [B]movies[/B]"): the sort's phrase with the item's
    name in bold. The spotlight's own label wins, unless it is just the item's name (it then said only "SETS")."""
    name = xbmc.getInfoLabel('Container(9000).ListItem.Property(plain)') or \
        re.sub(r'\[/?UPPERCASE\]', '', xbmc.getInfoLabel('Container(9000).ListItem.Label'))
    name = name.strip()
    own = xbmc.getInfoLabel('Skin.String(aeon.sp2.%s.label)' % sec).strip()
    if own and own.lower() != name.lower():
        return ''
    if not name:
        return ''
    sort = xbmc.getInfoLabel('Skin.String(aeon.sp2.%s.sort)' % sec) or 'random'
    try:
        import xbmcaddon
        tpl = xbmcaddon.Addon('skin.aeon.fuse').getLocalizedString(CUSTOM_HEAD_IDS.get(sort, 32433))
    except Exception:
        tpl = ''
    if '%s' not in (tpl or ''):
        tpl = 'Random %s'
    return tpl.replace('%s', '[B]%s[/B]' % name, 1)


def publish_heads(state):
    """Home header (skin 0.32.0): the spotlight's category (aeon.head.sp2) and the strip's category (aeon.head.cat),
    each with its last word in bold, while Home is on screen."""
    if not xbmc.getCondVisibility('Window.IsActive(home)'):
        return
    sec = xbmc.getInfoLabel('Container(9000).ListItem.Label2')
    sp2 = bold_last(xbmc.getInfoLabel('$VAR[Aeon_SP2Label_%s]' % sec)) if sec in SPOT_SECTIONS else ''
    if sec.startswith('custom') and sec in SPOT_SECTIONS:
        sp2 = custom_head(sec) or sp2
    cat = bold_last(xbmc.getInfoLabel('$VAR[Aeon_H_CatLabel]'))
    home = xbmcgui.Window(10000)
    for key, value in (('aeon.head.sp2', sp2), ('aeon.head.cat', cat)):
        if state.get(key) != value:
            state[key] = value
            home.setProperty(key, value)


LIBRARY_WINDOWS = (10000, 10025, 10502, 12005, 12006)    # Home, videos, music, full-screen video, visualisation


_POSTER_WIDE = {}


def check_osd_poster(state):
    """Player overlays (0.3.62): Window(Home).Property(aeon.osd.noseasonposter) = 1 while the playing episode's season
    poster is wider than tall (a library had a 500 x 281 landscape picture saved as season06-poster), so the skin shows
    the show's poster instead of cutting the picture to the 2:3 frame. Each picture is measured once (Pillow)."""
    home = xbmcgui.Window(10000)
    path = xbmc.getInfoLabel('Player.Art(season.poster)') if xbmc.getCondVisibility('Player.HasVideo') else ''
    if path == state.get('osdposter'):
        return
    state['osdposter'] = path
    wide = False
    if path:
        wide = _POSTER_WIDE.get(path)
        if wide is None:
            wide = False
            try:
                import io as _io
                from PIL import Image
                f = xbmcvfs.File(path)
                data = bytes(f.readBytes())
                f.close()
                w, h = Image.open(_io.BytesIO(data)).size
                wide = w > h
            except Exception as exc:
                xbmc.log('[script.aeon.helper] season poster not measured (%s): %s' % (exc, path), xbmc.LOGDEBUG)
            _POSTER_WIDE[path] = wide
    if wide:
        home.setProperty('aeon.osd.noseasonposter', '1')
    else:
        home.clearProperty('aeon.osd.noseasonposter')


def collect_backdrops(state):
    """Settings backdrop (skin 0.32.0): keep the fanart of what Home shows (spotlights, strips) in a pool, seeded once
    with a few random library titles; each time another window opens, Window(Home).Property(aeon.bgfan) gets a random
    one from the pool (the settings screens show it behind their picture)."""
    pool = state.setdefault('bgpool', [])
    if not state.get('bgseeded'):
        state['bgseeded'] = True
        for method, key in (('VideoLibrary.GetMovies', 'movies'), ('VideoLibrary.GetTVShows', 'tvshows')):
            try:
                found = (rpc(method, {'properties': ['art'], 'sort': {'method': 'random'}, 'limits': {'start': 0, 'end': 8}}).get('result') or {}).get(key) or []
            except Exception:
                found = []
            for item in found:
                pool[:] = backdrops.add(pool, (item.get('art') or {}).get('fanart'))
    if xbmc.getCondVisibility('Window.IsActive(home)'):
        sec = xbmc.getInfoLabel('Container(9000).ListItem.Label2')
        for cid in (boxart.spot_list(sec), 9301, 9302, 9303):
            if cid and xbmc.getCondVisibility('Control.IsVisible(%d)' % cid):
                art = xbmc.getInfoLabel('Container(%d).ListItem.Art(fanart)' % cid) or xbmc.getInfoLabel('Container(%d).ListItem.Art(tvshow.fanart)' % cid)
                pool[:] = backdrops.add(pool, art)
    window = xbmcgui.getCurrentWindowId()
    if window != state.get('bgwindow'):
        state['bgwindow'] = window
        if window not in LIBRARY_WINDOWS or not xbmcgui.Window(10000).getProperty('aeon.bgfan'):
            home = xbmcgui.Window(10000)
            home.setProperty('aeon.bgfan', backdrops.pick(pool, home.getProperty('aeon.bgfan')))


def publish_fav_stamp(state):
    """Home > Favourites (skin 0.32.0): Window(Home).Property(aeon.fav.stamp) changes whenever Kodi's favourites change
    (checked every 3 s while Home is on screen). The skin puts it in the row's path: Kodi reloads a plugin list only
    when its path changes, so a favourite added from the context menu shows up at once."""
    now = time.time()
    if now - state.get('favcheck', 0) < 3 or not xbmc.getCondVisibility('Window.IsActive(home)'):
        return
    state['favcheck'] = now
    try:
        favs = (rpc('Favourites.GetFavourites', {'properties': ['window', 'windowparameter', 'path', 'thumbnail']}).get('result') or {}).get('favourites') or []
    except Exception:
        return
    import hashlib
    stamp = hashlib.md5(json.dumps(favs, sort_keys=True).encode('utf-8')).hexdigest()[:10]
    if state.get('favstamp') != stamp:
        state['favstamp'] = stamp
        xbmcgui.Window(10000).setProperty('aeon.fav.stamp', stamp)


# skin settings that used to be called daylight.* (renamed in skin 0.11.0): old name -> new name
OLD_BOOLS = {'hidetrailer': 'hidetrailer', 'noartcolour': 'noartcolor', 'noweather': 'noweather', 'reducemotion': 'reducemotion'}
OLD_STRINGS = {'accent': 'dlaccent', 'artbackground': 'artbackground', 'bedtime': 'bedtime', 'focusoutline': 'focusoutline',
               'home.newest': 'home.newest', 'mood': 'mood', 'offsetbar': 'offsetbar', 'osdhide': 'osdhide',
               'spotlightrotate': 'spotlightrotate', 'watchedmarkers': 'watchedmarkers'}


def migrate_settings():
    """One time: carry the user's daylight.* skin settings over to their aeon.* names."""
    if xbmc.getSkinDir() != 'skin.aeon.fuse' or xbmc.getCondVisibility('Skin.HasSetting(aeon.migrated)'):
        return
    for old, new in OLD_BOOLS.items():
        if xbmc.getCondVisibility('Skin.HasSetting(daylight.%s)' % old):
            xbmc.executebuiltin('Skin.SetBool(aeon.%s)' % new)
    for old, new in OLD_STRINGS.items():
        value = xbmc.getInfoLabel('Skin.String(daylight.%s)' % old)
        if value:
            xbmc.executebuiltin('Skin.SetString(aeon.%s,%s)' % (new, value))
    xbmc.executebuiltin('Skin.SetBool(aeon.migrated)')


ROWS = 9            # rows of the Artist rows view (list 532)


def publish_row_counts(counts, shown):
    """Artist rows: the album count of the artist on each screen row -> Window(Home).Property(aeon.ac.<row>).
    A list row cannot look a number up by its own id, so the skin draws one label per screen row over the list."""
    home = xbmcgui.Window(10000)
    active = xbmc.getCondVisibility('Window.IsActive(music) + Control.IsVisible(532) + Container.Content(artists)')
    for row in range(ROWS):
        value = ''
        if active:
            dbid = xbmc.getInfoLabel('Container(532).ListItemPosition(%d).DBID' % row)
            number = counts.get(dbid)
            value = str(number) if number else ''
        if shown.get(row) != value:
            shown[row] = value
            home.setProperty('aeon.ac.%d' % row, value)


TRACK_ROWS = 5


def publish_track_counts(cache, shown):
    """Music Fanart list (513) of albums: the track count of the album on each screen row -> aeon.tc.<row>, and of the
    focused one -> aeon.tc.focus (skin 0.34.0). Counted once per album and kept."""
    home = xbmcgui.Window(10000)
    active = xbmc.getCondVisibility('Window.IsActive(music) + Control.IsVisible(513) + Container.Content(albums)')
    values = {}
    for row in range(TRACK_ROWS):
        values['aeon.tc.%d' % row] = ''
    values['aeon.tc.focus'] = ''
    if active:
        if len(cache) > 5000:
            cache.clear()
        wanted = [('aeon.tc.%d' % row, xbmc.getInfoLabel('Container(513).ListItemPosition(%d).DBID' % row)) for row in range(TRACK_ROWS)]
        wanted.append(('aeon.tc.focus', xbmc.getInfoLabel('Container(513).ListItem.DBID')))
        for name, dbid in wanted:
            if not dbid.isdigit():
                continue
            if dbid not in cache:
                cache[dbid] = album_tracks(rpc, dbid)
            values[name] = str(cache[dbid]) if cache[dbid] else ''
    for name, value in values.items():
        if shown.get(name) != value:
            shown[name] = value
            home.setProperty(name, value)


def publish_spot_logo(state):
    """Home spotlight (skin 0.34.0): when the library names a clearlogo file that is no longer there, the skin drew an
    empty logo box and no title. The logo of the item on screen is looked for once (in a thread; NFS can be slow) and
    a missing one is published as Window(Home).Property(aeon.sp2.nologo), so the title shows instead."""
    home = xbmcgui.Window(10000)
    path = ''
    if xbmc.getCondVisibility('Window.IsActive(home) + !System.ScreenSaverActive'):
        cid = boxart.spot_list(xbmc.getInfoLabel('Container(9000).ListItem.Label2'))
        if cid:
            path = (xbmc.getInfoLabel('Container(%d).ListItem.Art(clearlogo)' % cid) or
                    xbmc.getInfoLabel('Container(%d).ListItem.Art(tvshow.clearlogo)' % cid))
    missing = ''
    if path and not path.lower().startswith(('http://', 'https://')):
        known = state.setdefault('logo_ok', {})
        if path in known:
            missing = '' if known[path] else path
        elif not state.get('logo_busy'):
            if len(known) > 3000:
                known.clear()

            def check(target=path):
                real = target
                if real.startswith('image://'):
                    from urllib.parse import unquote
                    real = unquote(real[8:]).rstrip('/')
                try:
                    known[target] = bool(xbmcvfs.exists(real))
                except Exception:                 # cannot tell: leave the logo
                    known[target] = True
                finally:
                    state['logo_busy'] = False
            state['logo_busy'] = True
            threading.Thread(target=check, name='aeon-logocheck').start()
    if state.get('logo_missing') != missing:
        state['logo_missing'] = missing
        home.setProperty('aeon.sp2.nologo', missing)


def publish_uptime(shown):
    """Uptime as 8d 15h 2m -> Window(Home).Property(aeon.uptime / aeon.totaluptime)."""
    home = xbmcgui.Window(10000)
    for name, label in (('aeon.uptime', 'System.Uptime'), ('aeon.totaluptime', 'System.TotalUptime')):
        value = short_uptime(xbmc.getInfoLabel(label))
        if shown.get(name) != value:
            shown[name] = value
            home.setProperty(name, value)


class Cinema(xbmc.Player):
    """Cinema mode (Skin.String(aeon.cinema) = 1 / 2 / 3 trailers, empty = off): when a library film is started from the
    beginning, play trailers of new and upcoming films first. The film is stopped and started again as the last item of
    a playlist, so Stop during a trailer ends the session and Next skips a trailer.

    The trailers come from TMDb Helper's "In cinemas now" and "Upcoming" lists (YouTube paths). The pool is fetched in
    the background at most twice a day and kept in the add-on's data folder; with an empty pool the film just plays."""
    REFRESH = 12 * 3600

    def __init__(self):
        super(Cinema, self).__init__()
        self.busy = False
        self.pool = None
        self.checked = 0
        folder = xbmcvfs.translatePath('special://profile/addon_data/script.aeon.helper/')
        if not xbmcvfs.exists(folder):
            xbmcvfs.mkdirs(folder)
        self.path = os.path.join(folder, 'cinema.json')

    @staticmethod
    def count():
        if xbmc.getSkinDir() != 'skin.aeon.fuse':
            return 0
        return cinema.wanted(xbmc.getInfoLabel('Skin.String(aeon.cinema)'))

    def load(self):
        try:
            with open(self.path, 'r') as handle:
                data = json.load(handle)
            return data.get('pool') or [], float(data.get('time') or 0)
        except (IOError, OSError, ValueError):
            return [], 0

    def tick(self):
        """From the service loop: keep the pool fresh while cinema mode is on. Never during playback."""
        if not self.count() or time.time() - self.checked < 600 or self.isPlaying():
            return
        self.checked = time.time()
        pool, stamp = self.load()
        if self.pool is None:
            self.pool = pool
        if time.time() - stamp < self.REFRESH and pool:
            return
        if not xbmc.getCondVisibility('System.AddonIsEnabled(plugin.video.themoviedb.helper)'):
            return
        files = []
        for name in cinema.LISTS:
            reply = rpc('Files.GetDirectory', {'directory': cinema.PLUGIN % name, 'media': 'video', 'properties': ['title', 'premiered', 'trailer']})
            files.extend(reply.get('result', {}).get('files') or [])
        fresh = cinema.build_pool(files, datetime.date.today())
        if fresh:
            self.pool = fresh
            try:
                with open(self.path, 'w') as handle:
                    json.dump({'time': time.time(), 'pool': fresh}, handle)
            except (IOError, OSError):
                pass

    def onAVStarted(self):
        count = self.count()
        if self.busy or not count or not self.pool:
            return
        try:
            if not self.isPlayingVideo():
                return
            tag = self.getVideoInfoTag()
            movieid = tag.getDbId()
            size = xbmc.PlayList(xbmc.PLAYLIST_VIDEO).size()
            if not cinema.should_intercept(tag.getMediaType(), movieid, size, self.getTime()):
                return
        except RuntimeError:
            return
        trailers = cinema.pick(self.pool, count, datetime.date.today())
        if not trailers:
            return
        self.busy = True
        try:
            self.stop()
            for _ in range(30):
                if not self.isPlaying():
                    break
                xbmc.sleep(100)
            rpc('Playlist.Clear', {'playlistid': 1})
            for film in trailers:
                rpc('Playlist.Add', {'playlistid': 1, 'item': {'file': film['trailer']}})
            rpc('Playlist.Add', {'playlistid': 1, 'item': {'movieid': movieid}})
            rpc('Player.Open', {'item': {'playlistid': 1, 'position': 0}})
        finally:
            self.busy = False



class ArtTypeWatch(object):
    """Information page > Choose art (skin 0.39.11): Kodi's art-type list (DialogSelect) and the image picker after it
    (FileBrowser) both say "Choose art". While the type list is open over an information page, a short-lived thread
    follows its focused type every 50 ms and keeps it in Window(Home) aeon.arttype; the picker's heading then reads
    "Choose art · Poster". The skin's unload actions cannot catch the pick: Kodi empties the list before they run.
    The skin clears the property when the picker or the information page closes."""
    OPEN = 'Window.IsVisible(selectdialog) + Window.IsVisible(movieinformation)'

    def __init__(self):
        self.thread = None

    def tick(self):
        if self.thread is not None and self.thread.is_alive():
            return
        if xbmc.getCondVisibility(self.OPEN + ' + !String.IsEmpty(Container(6).ListItem.Property(type))'):
            self.thread = threading.Thread(target=self.follow, name='aeon-arttype')
            self.thread.start()

    def follow(self):
        home = xbmcgui.Window(10000)
        monitor = xbmc.Monitor()
        while xbmc.getCondVisibility(self.OPEN):
            label = xbmc.getInfoLabel('Container(6).ListItem.Label')
            # only items of the art-type list carry a type; an emptied list (the dialog closing) changes nothing
            if label and xbmc.getInfoLabel('Container(6).ListItem.Property(type)') and home.getProperty('aeon.arttype') != label:
                home.setProperty('aeon.arttype', label)
            if monitor.waitForAbort(0.05):
                return


class MemoryTrim(object):
    """Kodi on Linux keeps the memory it frees in its malloc arenas instead of handing it back: on the 4 GB CoreELEC box
    Kodi stood at 2.4 GB on an idle Home screen, ran out of memory while paging the film list and hung. One malloc_trim
    brought it from 2,367 MB to 1,191 MB. The user picks when (Skin settings > Motion, memory, reset > Memory hand-back):
    when free RAM gets low (default: keep 1 GB free) or after the keys have rested a number of seconds. A trim holds
    Kodi's allocator for 40-260 ms. Around videos: once as one starts and once when it stops; while it plays only
    after free memory has stayed under the minimum for 10 s. memtrim.decide has the rules; checked every second."""
    CHECK_S = 1

    def __init__(self):
        from resources.lib import memtrim
        self.memtrim = memtrim
        self.ok = memtrim.available()
        self.next_check = 0
        self.last_at = 0
        self.last_freed = None
        self.armed = False      # a key was used since the last rest (idle mode)
        self.video = False
        self.low_since = None   # free memory at or under the minimum since then

    def tick(self):
        if not self.ok:
            return
        now = time.time()
        if now < self.next_check:
            return
        self.next_check = now + self.CHECK_S
        mode, idle_s, free_mb = self.memtrim.settings(xbmc.getInfoLabel('Skin.String(aeon.memtrim.mode)'),
                                                      xbmc.getInfoLabel('Skin.String(aeon.memtrim.idle)'),
                                                      xbmc.getInfoLabel('Skin.String(aeon.memtrim.free)'))
        total, available = self.memtrim.meminfo_mb()
        video = xbmc.getCondVisibility('Player.HasVideo')
        edge = self.memtrim.video_edge(self.video, video, now, self.last_at)
        self.video = video
        if available is not None and available <= free_mb:
            self.low_since = self.low_since or now
        else:
            self.low_since = None
        rested = xbmc.getCondVisibility('System.IdleTime(%d)' % idle_s)
        if not rested:
            self.armed = True
        verdict = edge or self.memtrim.decide(mode, available, now, self.last_at, self.last_freed,
                                              paused=xbmc.getCondVisibility('System.IdleTime(2)'),
                                              rested=rested and self.armed, video=video, free_mb=free_mb,
                                              low_since=self.low_since)
        if not verdict:
            return
        self.armed = False
        self.low_since = None
        before = self.memtrim.rss_mb()
        started = time.time()
        self.memtrim.trim()
        after = self.memtrim.rss_mb()
        self.last_at = time.time()
        self.last_freed = (before - after) if before and after else 0
        xbmc.log('[script.aeon.helper] memory handed back (%s): Kodi %s MB -> %s MB, system %d of %d MB in use before '
                 '(%.0f ms)' % ('video ' + verdict if verdict in ('start', 'stop') else mode, before, after,
                                total - available, total, (self.last_at - started) * 1000), xbmc.LOGINFO)


class DolbyVision(object):
    """The Dolby Vision profile chip (P5, P7 FEL, P7 MEL, P8.1, P8.4 ...): the side files of the film in focus are read
    once (in a thread) and remembered."""

    def __init__(self):
        self.seen = None
        self.known = {}
        self.busy = set()

    def publish(self, path, value):
        home = xbmcgui.Window(10000)
        home.setProperty('aeon.dvp', value)
        home.setProperty('aeon.dvp.path', path if value else '')

    def read(self, path):
        value = ''
        nfo_read = False
        try:
            for kind, side in dvprofile.side_paths(path):
                if kind == 'nfo' and nfo_read:
                    continue                      # only the first .nfo that exists counts
                if not xbmcvfs.exists(side):
                    continue
                handle = xbmcvfs.File(side)
                try:
                    text = handle.read()
                finally:
                    handle.close()
                value = dvprofile.label(text) if kind == 'nfo' else dvprofile.label_cmm(text)
                nfo_read = nfo_read or kind == 'nfo'
                if value:
                    break
        except Exception as error:               # an unreadable side file only means no chip
            xbmc.log('[script.aeon.helper] nfo: %s' % error, xbmc.LOGDEBUG)
        self.known[path] = value
        self.busy.discard(path)
        if xbmc.getInfoLabel('ListItem.FileNameAndPath') == path:
            self.publish(path, value)

    def tick(self):
        if xbmc.getInfoLabel('ListItem.HdrType') != 'dolbyvision':
            if self.seen:
                self.seen = None
                self.publish('', '')
            return
        path = xbmc.getInfoLabel('ListItem.FileNameAndPath')
        if path == self.seen:
            return
        self.seen = path
        if path in self.known:
            self.publish(path, self.known[path])
        elif path not in self.busy:
            self.busy.add(path)
            threading.Thread(target=self.read, args=(path,)).start()

STUDIO_SOURCES = (('aeon.studio', 'ListItem.Studio'), ('aeon.ss.studio', 'Container(9701).ListItem.Studio'))


def publish_studios(state):
    """The first studio of the item in focus (aeon.studio; the information page) and of the screensaver's slide
    (aeon.ss.studio), each with the full text it came from (<name>.of): the skin shows a logo only while that still
    matches, so a logo never belongs to the item before."""
    from resources.lib import studio
    home = xbmcgui.Window(10000)
    for prop, label in STUDIO_SOURCES:
        full = xbmc.getInfoLabel(label)
        if state.get(prop) == full:
            continue
        state[prop] = full
        home.setProperty(prop, studio.first(full))
        home.setProperty(prop + '.of', full)


def manifest_check():
    """Files copied over by hand (a new version of this helper or of the skin): Kodi keeps reading its old copy of
    addon.xml, so new context menu items or a new version stay unknown until UpdateLocalAddons runs. Run it once when
    the version on disk differs from the one Kodi has registered."""
    import re
    import xbmcaddon
    for addon_id in ('script.aeon.helper', 'skin.aeon.fuse'):
        try:
            addon = xbmcaddon.Addon(addon_id)
            path = os.path.join(xbmcvfs.translatePath(addon.getAddonInfo('path')), 'addon.xml')
            with open(path, encoding='utf-8') as handle:
                head = handle.read(800)
            found = re.search(r'<addon\b[^>]*\bversion="([^"]+)"', head)
        except Exception:  # noqa: BLE001 - not installed / unreadable
            continue
        if found and found.group(1) != addon.getAddonInfo('version'):
            xbmc.log('[script.aeon.helper] %s %s on disk, %s registered: UpdateLocalAddons'
                     % (addon_id, found.group(1), addon.getAddonInfo('version')), xbmc.LOGINFO)
            xbmc.executebuiltin('UpdateLocalAddons')
            return


def run():
    # one instance only: a newer start (add-on re-enabled / updated) takes over and this one ends
    token = str(time.time())
    xbmcgui.Window(10000).setProperty('aeon.helper.token', token)
    monitor = Monitor()
    manifest_check()
    migrate_settings()
    # the library may still be opening at start-up
    if monitor.waitForAbort(10):
        return
    # the user's per-section fonts, after a skin update put a fresh Font.xml in place
    import fontpick
    fontpick.sync()
    publish()
    artist_albums = album_counts(rpc)
    row_counts = {}
    track_cache = {}
    track_shown = {}
    uptimes = {}
    last_counts = time.time()
    last_aired = time.time()
    last_played = time.time()          # start-up counts as activity: the first read is three quiet minutes in at the soonest
    seen = None
    seen_containers = {}
    seen_player = None
    shown_options = {}
    themes = Themes()
    trailers = Cinema()
    dolby = DolbyVision()
    studios = {}
    memory = MemoryTrim()
    art_types = ArtTypeWatch()
    chapter_pictures = chapterwin.ChapterPictures()
    palette = {}
    try:
        menufile.ensure_android()
    except Exception as error:               # never let a menu file stop the service
        xbmc.log('[script.aeon.helper] Power row: %s' % error, xbmc.LOGINFO)
    refresh_artists(monitor)
    refresh_videos(monitor)
    while not monitor.waitForAbort(POLL):
        if xbmcgui.Window(10000).getProperty('aeon.helper.token') != token:
            return
        publish_view_options(shown_options)
        themes.tick()
        sync_theme(palette)
        if xbmc.Player().isPlaying():                 # playing or paused: the Planner read waits for the quiet after it
            last_played = time.time()
        arrfeed.tick(palette, xbmc.Player().isPlaying())
        if time.time() - last_aired >= 60:            # looks every minute; reads only when the list is due and it is quiet
            last_aired = time.time()
            refresh_nextaired(monitor, last_played)
        trailers.tick()
        dolby.tick()
        publish_studios(studios)
        memory.tick()
        art_types.tick()
        chapter_pictures.tick()
        logocache.tick(palette)
        blurcache.tick(palette)
        searchhist.tick(palette)
        nextaired.publish_week(palette)
        publish_heads(palette)
        check_osd_poster(palette)
        collect_backdrops(palette)
        publish_fav_stamp(palette)
        sync_karmamole(palette)
        sync_spot_container(palette)
        publish_row_counts(artist_albums, row_counts)
        publish_track_counts(track_cache, track_shown)
        publish_spot_logo(palette)
        publish_uptime(uptimes)
        if time.time() - last_counts >= COUNT_INTERVAL:
            publish()
            artist_albums = album_counts(rpc)
            last_counts = time.time()
        # the item the skin is showing: Home properties follow it (all ratings, not only the default one)
        key = (xbmc.getInfoLabel('ListItem.DBType'), xbmc.getInfoLabel('ListItem.DBID'))
        if key != seen:
            seen = key
            publish_ratings(fetch_ratings(rpc, *key))
        # the video playing: its ratings for the player overlays (aeon.r.player.*); VideoPlayer.Rating(name) only
        # ever returns the default rating
        pkey = player_key()
        if pkey != seen_player:
            seen_player = pkey
            publish_ratings(fetch_ratings(rpc, *pkey) if pkey[1] else {}, 'player')
        for cid in CONTAINERS:
            ckey = (xbmc.getInfoLabel('Container(%d).ListItem.DBType' % cid),
                    xbmc.getInfoLabel('Container(%d).ListItem.DBID' % cid))
            if seen_containers.get(cid) != ckey:
                seen_containers[cid] = ckey
                publish_ratings(fetch_ratings(rpc, *ckey), cid)
                xbmcgui.Window(10000).setProperty('aeon.epm.%d' % cid, fetch_epmark(rpc, *ckey))


if __name__ == '__main__':
    run()
