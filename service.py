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
import searchwin
import smoothprog
import timeleft
import addonart
import musicbio
import epcomb
import focusart
import setrow
import guiread
import videocache
from resources.lib import backdrops, boxart, cinema, dvprofile, mediainfo, multiep, planner
from resources.lib import round3          # 0.3.118: round-3 Fused Glass style windows
from resources.lib import fgsfacts        # 0.3.117: facts for the Fused Glass style windows
from resources.lib import skchapters      # 0.3.112: Skippy's segments as chapters on the player's bar
from resources.lib.counts import album_counts, album_tracks, fetch_counts
from resources.lib.episodes import fetch_epmark
from resources.lib.headline import bold_last
from resources.lib.ratings import NAMES, fetch_ratings
from resources.lib.themes import find_theme
from resources.lib.uptime import short as short_uptime, from_seconds, system_seconds, health as read_health
from resources.lib import sysinfo

PREFIX = 'aeon.count.'
RATING_PREFIX = 'aeon.r.'
# containers the skin reads by number (Home spotlight / strips, set and version panes)
CONTAINERS = (9301, 9302, 9421, 9422, 5221, 5241, 5224, 5244, 5104, 5101, 9441, 538)   # 538: Episode combined (0.3.75)
COUNT_INTERVAL = 600
POLL = 0.3


def rpc(method, params):
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return json.loads(xbmc.executeJSONRPC(request))


def publish():
    home = xbmcgui.Window(10000)
    language = xbmc.getLanguage(xbmc.ISO_639_1)
    for name, value in fetch_counts(rpc).items():
        home.setProperty(PREFIX + name, str(value))
        # 0.3.73 Fused Home > System: the same number with a thousands separator (aeon.countg.movies = "6,123")
        home.setProperty('aeon.countg.' + name, sysinfo.grouped(value, language))


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


def sync_palbase(state):
    """Skin.String(aeon.palbase): the name of the palette in use without its scope ("Nord" for "Nord (menus)"), for the
    skin's label (Aeon_PaletteName). Kept in step here too, for a palette chosen in Kodi's own Colours list."""
    value = xbmc.getInfoLabel('Skin.CurrentColourTheme')
    if value == state.get('colours'):
        return
    state['colours'] = value
    from resources.lib import palscope
    name = palscope.split(value)[0]
    if name != xbmc.getInfoLabel('Skin.String(aeon.palbase)'):
        xbmc.executebuiltin('Skin.SetString(aeon.palbase,%s)' % name)


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
TIME_LEFT = timeleft.TimeLeft()          # "x min left" on list rows (skin 0.56.8)
ADDON_ART = addonart.AddonArt()          # add-on screenshots / settings fanart (skin 0.56.9)
MUSIC_BIO = musicbio.MusicBio()          # album / artist bio for albums and song lists (skin 0.56.11)


class Monitor(xbmc.Monitor):
    def onNotification(self, sender, method, data):
        # library art with the wrong shape (a landscape picture as a season poster): checked once Kodi is quiet
        if method == 'VideoLibrary.OnUpdate':
            ART_GUARD.queue(data)
        if method in ('VideoLibrary.OnUpdate', 'VideoLibrary.OnRemove', 'Player.OnStop'):
            TIME_LEFT.wake()

    def onScanFinished(self, library):
        publish()
        if library == 'music':
            refresh_artists(self, force=True)
        if library == 'video':
            refresh_videos(self, force=True)
            TIME_LEFT.wake()

    def onCleanFinished(self, library):
        publish()


VIEW_OPTIONS = ('ratings', 'mediainfo', 'plot', 'bg', 'strip', 'bgs', 'bio', 'art', 'counts', 'watched', 'trailer', 'boxbg', 'rings', 'logos',
                'fop', 'fblur', 'ftint',          # 0.3.108 (skin 0.56.42): the library fanart's opacity / blur / tint per view
                'pshadow', 'pop', 'pblur', 'ptint')    # 0.3.111 (skin 0.56.45): the panels' shadow / opacity / blur / tint per view


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


def focus_item():
    """In a library window ListItem is always the view's own list, also while the focus is in a second list of the view
    (the episodes of Combined, the Season list or Episode combined): then that list's item, when it holds library items
    (skin 0.51.0: Backdrop = Colors follows the episode thumbs there)."""
    cid = xbmc.getInfoLabel('System.CurrentControlId')
    if cid.isdigit() and xbmc.getInfoLabel('Container(%s).ListItem.DBType' % cid):
        return 'Container(%s).ListItem' % cid
    return 'ListItem'


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
    # the Fused Glass Planner with Background = Colors (0.3.76): KarmaMole makes the soft colour picture of its list too
    planner = xbmc.getCondVisibility('Window.IsActive(1168) + Skin.HasSetting(aeon.fglass) + String.IsEmpty(Skin.String(aeon.planner.bg))')
    wash = installed and (page or planner or 'color' in [xbmc.getInfoLabel('Skin.String(aeon.%s)' % x) for x in ('ssbg', 'spbg', 'wsbg')])
    want = ','.join(name for name, on in (('colours', boxes or wash), ('softart', wash)) if on)
    if home.getProperty('KarmaMole.Helper.Features') != want:
        home.setProperty('KarmaMole.Helper.Features', want)
    colour = ''
    artcol = soft = ''
    if (boxes or page) and in_library:
        art = ''
        item = focus_item()
        for key in boxart.art_keys(xbmc.getInfoLabel('%s.DBType' % item)):
            art = xbmc.getInfoLabel('%s.Art(%s)' % (item, key))
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
    elif xbmc.getCondVisibility('Window.IsActive(1168) + Skin.HasSetting(aeon.fglass) + String.IsEmpty(Skin.String(aeon.planner.bg))'):
        # Fused Glass Planner, Background = Colors (0.3.74): the list in focus, else the selected day's column
        cid = xbmc.getInfoLabel('System.CurrentControlId')
        if cid not in ('9500',) + tuple(str(9510 + n) for n in range(1, 8)):
            col = xbmcgui.Window(10000).getProperty('aeon.planner.col') or '1'
            cid = '9500' if xbmcgui.Window(10000).getProperty('aeon.planner.mode') == 'day' else str(9510 + int(col))
        if xbmc.getCondVisibility('Integer.IsGreater(Container(%s).NumItems,0)' % cid):
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


SPOT_SECTIONS = ('movies', 'tv', 'music') + tuple('custom%d' % k for k in range(1, 11))      # ten custom items since 0.3.86
# custom spotlights (0.3.61): the heading by sort, from the skin's templates 32433-32439 ("Random %s"), %s = item name
CUSTOM_HEAD_IDS = {'random': 32433, 'dateadded': 32434, 'lastplayed': 32435, 'rating': 32436, 'playcount': 32437,
                   'year': 32438, 'title': 32439}
# what the skin's spotlight list holds while "Home spotlight: recently watched sets" applies (Aeon_SP2List_<sec>)
RECENT_SETS = 'plugin://script.aeon.helper/?info=recentsets'


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
    if xbmc.getInfoLabel('$VAR[Aeon_SP2List_%s]' % sec).startswith(RECENT_SETS):
        sort = 'lastplayed'          # "Home spotlight: recently watched sets" is on for this item (skin 0.45.2)
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


ROWS = 10           # rows of the Artist rows view (list 532; ten in Fused Glass, 0.3.80)


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
    focused one -> aeon.tc.focus (skin 0.34.0). Counted once per album and kept. Album list (532, skin 0.56.8, the list
    row rule: the track count at the right of every album row): aeon.tc532.<row> for its ROWS screen rows."""
    home = xbmcgui.Window(10000)
    active = xbmc.getCondVisibility('Window.IsActive(music) + Control.IsVisible(513) + Container.Content(albums)')
    active532 = xbmc.getCondVisibility('Window.IsActive(music) + Control.IsVisible(532) + Container.Content(albums)')
    # skin 0.56.14: the focused album's count for the info strip of the Album wall, Cover showcase and Artist wall
    # (530 / 531 / 534) too
    other = 0
    if not (active or active532) and xbmc.getCondVisibility('Window.IsActive(music) + Container.Content(albums)'):
        other = next((cid for cid in (530, 531, 534) if xbmc.getCondVisibility('Control.IsVisible(%d)' % cid)), 0)
    values = {}
    for row in range(TRACK_ROWS):
        values['aeon.tc.%d' % row] = ''
    for row in range(ROWS):
        values['aeon.tc532.%d' % row] = ''
    values['aeon.tc.focus'] = ''
    if active or active532 or other:
        if len(cache) > 5000:
            cache.clear()
        wanted = []
        if active:
            wanted = [('aeon.tc.%d' % row, xbmc.getInfoLabel('Container(513).ListItemPosition(%d).DBID' % row)) for row in range(TRACK_ROWS)]
            wanted.append(('aeon.tc.focus', xbmc.getInfoLabel('Container(513).ListItem.DBID')))
        elif other:
            wanted = [('aeon.tc.focus', xbmc.getInfoLabel('Container(%d).ListItem.DBID' % other))]
        else:
            wanted = [('aeon.tc532.%d' % row, xbmc.getInfoLabel('Container(532).ListItemPosition(%d).DBID' % row)) for row in range(ROWS)]
            wanted.append(('aeon.tc.focus', xbmc.getInfoLabel('Container(532).ListItem.DBID')))
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
    """Uptime as 8d 15h 2m -> Window(Home).Property(aeon.uptime / aeon.totaluptime), and how long the machine itself has
    been on (0.3.73, Fused Home > Power / System): aeon.boxuptime."""
    home = xbmcgui.Window(10000)
    for name, label in (('aeon.uptime', 'System.Uptime'), ('aeon.totaluptime', 'System.TotalUptime')):
        value = short_uptime(xbmc.getInfoLabel(label))
        if shown.get(name) != value:
            shown[name] = value
            home.setProperty(name, value)
    value = from_seconds(system_seconds())
    if shown.get('aeon.boxuptime') != value:
        shown['aeon.boxuptime'] = value
        home.setProperty('aeon.boxuptime', value)
    # Fused Home > System (0.3.73): memory ring, memory text, the status pill and the processor (every 2 s), the
    # Kodi / OS / screen lines (every 30 s)
    now = time.time()
    if now - shown.get('_health', 0) < 2:
        return
    shown['_health'] = now
    publish_sysinfo(home, shown, now)
    status, pct, mem = read_health(xbmc.getInfoLabel('System.Memory(used.percent)'), xbmc.getInfoLabel('System.Memory(used)'),
                                   xbmc.getInfoLabel('System.Memory(total)'), xbmc.getInfoLabel('System.CPUTemperature'),
                                   xbmc.getInfoLabel('System.GPUTemperature'))
    cpu = sysinfo.cpu_average(xbmc.getInfoLabel('System.CPUUsage'))
    for name, val in (('aeon.health', status), ('aeon.mem.pct', pct), ('aeon.mem.text', mem), ('aeon.cpu.pct', cpu)):
        if shown.get(name) != val:
            shown[name] = val
            home.setProperty(name, val)


def publish_sysinfo(home, shown, now):
    """Fused Home > System, the This box card: aeon.sys.major ("22"), aeon.sys.tag ("RC2"), aeon.sys.osname
    ("CoreELEC"), aeon.sys.osline ("CoreELEC 22 Piers nightly, 13 November"), aeon.sys.device ("CoreELECAM9Pro") and
    aeon.sys.screen ("2160p · 24 Hz"). Read every 30 s (the screen mode can change)."""
    if now - shown.get('_sysinfo', 0) < 30:
        return
    shown['_sysinfo'] = now
    busy = xbmc.getLocalizedString(503)              # "Busy": Kodi is still working the label out, ask again in 3 s
    labels = dict((key, xbmc.getInfoLabel(key)) for key in ('System.BuildVersionShort', 'System.OSVersionInfo',
                                                            'System.FriendlyName', 'System.ScreenResolution'))
    for key, value in labels.items():
        if busy and value == busy:
            labels[key] = ''
            shown['_sysinfo'] = now - 27
    number, tag = sysinfo.major(labels['System.BuildVersionShort'])
    months = [xbmc.getLocalizedString(21 + i) for i in range(12)]
    osname, osline = sysinfo.os_line(labels['System.OSVersionInfo'], months if all(months) else None)
    values = (('aeon.sys.major', number), ('aeon.sys.tag', tag), ('aeon.sys.osname', osname), ('aeon.sys.osline', osline),
              ('aeon.sys.device', sysinfo.device(labels['System.FriendlyName'])),
              ('aeon.sys.screen', sysinfo.screen(labels['System.ScreenResolution'])))
    for name, val in values:
        if not val and shown.get(name):              # a label that went Busy keeps what was read before
            continue
        if shown.get(name) != val:
            shown[name] = val
            home.setProperty(name, val)


class OsdAlbum(object):
    """0.3.111 (skin 0.56.45): the album track list in the music player controls follows the playing library song
    (resources/lib/osdalbums.py); while another album of the artist is shown, a new song only updates "playing"."""

    def __init__(self):
        self.open = False
        self.song = ''

    def tick(self):
        is_open = bool(xbmc.getCondVisibility('Window.IsActive(musicosd) + Integer.IsGreater(MusicPlayer.DBID,0)'))
        song = xbmc.getInfoLabel('MusicPlayer.DBID') if is_open else ''
        if not is_open:
            self.open, self.song = False, ''
            return
        if self.open and song == self.song:
            return
        from resources.lib import osdalbums
        home = xbmcgui.Window(10000)
        try:
            if not self.open or home.getProperty('aeon.osd.alb.playing') or not home.getProperty('aeon.osd.alb.id'):
                osdalbums.follow_song(song)
            else:
                albumid, _artist = osdalbums.song_album(song)
                home.setProperty('aeon.osd.alb.playing', '1' if str(albumid) == home.getProperty('aeon.osd.alb.id') else '')
        except Exception as error:
            xbmc.log('[script.aeon.helper] osd album: %s' % error, xbmc.LOGINFO)
        self.open, self.song = True, song


class StartItem(object):
    """0.3.111 (skin 0.56.45) Skin settings > Home menu > Start on (Skin.String(aeon.startitem) = a Home menu key): once
    per start, when the start-up splash has gone (Window(Home).Property(aeon.splash) empty, Home open, its menu filled),
    the Home menu moves to that item. Home's items carry their key as Label2; read over JSON-RPC (main thread)."""
    CHECK_S = 0.5

    def __init__(self):
        self.done = False
        self.next_check = 0
        self.ready_since = 0

    @staticmethod
    def rpc(method, params):
        import json
        return json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method,
                                                          'params': params}))).get('result') or {}

    def tick(self):
        if self.done:
            return
        now = time.time()
        if now < self.next_check:
            return
        self.next_check = now + self.CHECK_S
        key = xbmc.getInfoLabel('Skin.String(aeon.startitem)')
        if not key or xbmc.getSkinDir() != 'skin.aeon.fuse':
            self.done = bool(xbmc.getCondVisibility('Window.IsActive(home)')) and not key
            return
        if not xbmc.getCondVisibility('Window.IsActive(home) + Integer.IsGreater(Container(9000).NumItems,0) + '
                                      'String.IsEmpty(Window(Home).Property(aeon.splash)) + Control.HasFocus(9000)'):
            self.ready_since = 0
            return
        if not self.ready_since:
            self.ready_since = now
            return
        if now - self.ready_since < 1.0:      # the splash's own SetFocus(9000) first
            return
        self.done = True
        count = int(xbmc.getInfoLabel('Container(9000).NumItems') or 0)
        labels = ['Container(9000).ListItemAbsolute(%d).Label2' % i for i in range(count)]
        got = self.rpc('XBMC.GetInfoLabels', {'labels': labels})
        for i, name in enumerate(labels):
            if got.get(name) == key:
                xbmc.executebuiltin('SetFocus(9000,%d,absolute)' % i)
                xbmc.log('[script.aeon.helper] Start on: %s (item %d)' % (key, i), xbmc.LOGINFO)
                return


class HomePreload(object):
    """Skin 0.56.4: Home's strips under Movies, TV shows and Music (9301-9303) load one after another after Kodi starts,
    so Down on those items finds them ready. A section loads once Window(Home) aeon.pl.<sec> is set; the skin sets it
    at once for the item that gets the focus (Timers.xml aeonhomearm) and then keeps that strip's titles. Here the next
    one is set when the last one is in (titles, or empty and quiet for 4 s, or 30 s), and only while Home is the open
    window (the lists of a closed window do not load), no dialog has the focus and no video plays.
    0.3.111 (skin 0.56.45): a section the skin armed first (Home opened on TV shows) is waited for too, not skipped, and
    each section that is in gets aeon.pl.<sec>.in: the start-up splash waits for those (it used to end after Movies,
    with TV shows still loading)."""
    ORDER = (('movies', 9301, 93911), ('tv', 9302, 93912), ('music', 9303, 93913))
    WAIT_S = 30
    CHECK_S = 0.5
    QUIET = 8                            # 4 s empty and not loading: an empty section (the node list may start late)

    def __init__(self):
        self.done = False
        self.current = None
        self.since = 0
        self.quiet = 0
        self.next_check = 0
        self.checked = set()

    def loaded(self, strip, node):
        if xbmc.getCondVisibility('Container(%d).IsUpdating | Container(%d).IsUpdating' % (node, strip)):
            self.quiet = 0
            return False
        if xbmc.getCondVisibility('Integer.IsGreater(Container(%d).NumItems,0)' % strip):
            return True
        self.quiet += 1                  # empty and not loading: an empty section, or the step between the two lists
        return self.quiet >= self.QUIET

    def tick(self):
        if self.done:
            return
        now = time.time()
        if now < self.next_check:
            return
        self.next_check = now + self.CHECK_S
        if xbmc.getSkinDir() != 'skin.aeon.fuse':
            return
        # Container(id) reads the window that has the focus: a dialog over Home (CoreELEC's release notes after an
        # update are not even modal) has none of these lists, so Home's menu list must be readable
        if not xbmc.getCondVisibility('Window.IsActive(home) + Integer.IsGreater(Container(9000).NumItems,0) + '
                                      '!Player.HasVideo'):
            self.since = now             # the wait counts only while the lists can load and be read
            self.quiet = 0
            return
        home = xbmcgui.Window(10000)
        if self.current:
            sec, strip, node = self.current
            if not self.loaded(strip, node) and now - self.since < self.WAIT_S:
                return
            xbmc.log('[script.aeon.helper] Home %s strip in after %.1f s (%s items)'
                     % (sec, now - self.since, xbmc.getInfoLabel('Container(%d).NumItems' % strip)), xbmc.LOGINFO)
            home.setProperty('aeon.pl.%s.in' % sec, '1')
            self.checked.add(sec)
            self.current = None
        # one at a time: a section that is still loading (the skin armed the focused one) goes first
        loading = [item for item in self.ORDER if item[0] not in self.checked and xbmc.getCondVisibility(
            'Container(%d).IsUpdating | Container(%d).IsUpdating' % (item[1], item[2]))]
        for item in loading + [item for item in self.ORDER if item not in loading]:
            if item[0] in self.checked:
                continue
            if not home.getProperty('aeon.pl.%s' % item[0]):
                home.setProperty('aeon.pl.%s' % item[0], '1')
            self.current, self.since, self.quiet = item, now, 0
            return
        self.done = True
        home.setProperty('aeon.pl.done', '1')   # skin 0.56.20: the start-up splash's Home rows step


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
        # the dialogs first (a plain read), the picker's item only while they are up (a main-thread read, guiread.py)
        if xbmc.getCondVisibility(self.OPEN) and xbmc.getCondVisibility('!String.IsEmpty(Container(6).ListItem.Property(type))'):
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


class MediaInfoSidecar(object):
    """0.3.97 Skin settings > Details > Media info from sidecars (Skin.HasSetting(aeon.mi.sidecar), off by default): the
    mediainfo sidecar of the film / episode in focus (Curator Media Manager's <name>.cmm_mediainfo.xml first, else
    tinyMediaManager's <name>-mediainfo.xml) is read once in a thread and remembered; aeon.mi.<key> holds what it says
    and aeon.mi.path the file it belongs to (the skin shows the values only while that is ListItem.FileNameAndPath)."""
    KEYS = ('from', 'source', 'format', 'vsource', 'vcodec', 'edition', 'res', 'hdr', '3d', 'video', 'container', 'size', 'bitrate', 'audio', 'audio.count',
            'audio.list', 'commentary', 'subs.count', 'subs.langs', 'sdh', 'chapters')
    TYPES = ('movie', 'episode', 'musicvideo')

    def __init__(self):
        self.seen = None
        self.known = {}
        self.busy = set()

    def publish(self, path, values):
        home = xbmcgui.Window(10000)
        for key in self.KEYS:
            home.setProperty('aeon.mi.' + key, values.get(key, '') if values else '')
        home.setProperty('aeon.mi.path', path if values else '')

    @staticmethod
    def language(code):
        try:
            return xbmc.convertLanguage(code, xbmc.ENGLISH_NAME) or code
        except Exception:
            return code

    def read(self, path):
        values = {}
        try:
            for kind, side in mediainfo.side_paths(path):
                if not xbmcvfs.exists(side):
                    continue
                handle = xbmcvfs.File(side)
                try:
                    text = handle.read()
                finally:
                    handle.close()
                info = mediainfo.parse(kind, text)
                if info:
                    values = mediainfo.props(info, self.language)
                    break
        except Exception as error:                # an unreadable sidecar only means nothing extra
            xbmc.log('[script.aeon.helper] mediainfo sidecar: %s' % error, xbmc.LOGDEBUG)
        if len(self.known) > 400:
            self.known.clear()
        self.known[path] = values
        self.busy.discard(path)
        if self.seen == path:
            self.publish(path, values)

    # 0.3.114: on Home the spotlight's item is in a list that never has focus (Aeon_Home: 9441 the big spotlight,
    # 9421-9423 the section spotlights); the sidecar of the one shown there is read when the focused item is no video
    SPOTS = (9441, 9421, 9422, 9423)

    def focused(self):
        """(prefix) of the item whose sidecar the skin can show now: the focused list item, else a Home spotlight's"""
        if xbmc.getInfoLabel('ListItem.DBType') in self.TYPES:
            return 'ListItem.'
        if xbmc.getCondVisibility('Window.IsActive(home)'):
            for cid in self.SPOTS:
                pfx = 'Container(%d).ListItem.' % cid
                if xbmc.getCondVisibility('Control.IsVisible(%d)' % cid) and xbmc.getInfoLabel(pfx + 'DBType') in self.TYPES:
                    return pfx
        return None

    def tick(self):
        pfx = self.focused() if xbmc.getCondVisibility('Skin.HasSetting(aeon.mi.sidecar)') else None
        if not pfx:
            if self.seen:
                self.seen = None
                self.publish('', {})
            return
        path = xbmc.getInfoLabel(pfx + 'FileNameAndPath')
        if path == self.seen:
            return
        self.seen = path
        if path in self.known:
            self.publish(path, self.known[path])
        elif path and path not in self.busy:
            self.busy.add(path)
            threading.Thread(target=self.read, args=(path,)).start()

class PlayerSidecar(object):
    """0.3.114 the video playing: its Dolby Vision profile (aeon.pf.dvp, "P8.1") and its mediainfo sidecar
    (aeon.pf.mi.<key>, the keys of MediaInfoSidecar) for the player's information page ("In this file", Video line),
    which showed only Kodi's plain "DV". Read once per file in a thread; cleared when no video plays."""
    KEYS = MediaInfoSidecar.KEYS

    def __init__(self):
        self.seen = None

    def publish(self, path, dvp, values):
        home = xbmcgui.Window(10000)
        home.setProperty('aeon.pf.dvp', dvp or '')
        for key in self.KEYS:
            home.setProperty('aeon.pf.mi.' + key, (values or {}).get(key, ''))
        home.setProperty('aeon.pf.mi.path', path if (dvp or values) else '')

    def read(self, path):
        dvp, values = '', {}
        try:
            nfo_read = False
            for kind, side in dvprofile.side_paths(path):
                if kind == 'nfo' and nfo_read:
                    continue
                if not xbmcvfs.exists(side):
                    continue
                handle = xbmcvfs.File(side)
                try:
                    text = handle.read()
                finally:
                    handle.close()
                dvp = dvprofile.label(text) if kind == 'nfo' else dvprofile.label_cmm(text)
                nfo_read = nfo_read or kind == 'nfo'
                if dvp:
                    break
            for kind, side in mediainfo.side_paths(path):
                if not xbmcvfs.exists(side):
                    continue
                handle = xbmcvfs.File(side)
                try:
                    text = handle.read()
                finally:
                    handle.close()
                info = mediainfo.parse(kind, text)
                if info:
                    values = mediainfo.props(info, MediaInfoSidecar.language)
                    break
        except Exception as error:               # an unreadable side file only means nothing extra
            xbmc.log('[script.aeon.helper] player sidecar: %s' % error, xbmc.LOGDEBUG)
        if self.seen == path:
            self.publish(path, dvp, values)

    def tick(self):
        if not xbmc.getCondVisibility('Player.HasVideo'):
            if self.seen:
                self.seen = None
                self.publish('', '', {})
            return
        path = xbmc.getInfoLabel('Player.FilenameAndPath')
        if not path or path == self.seen:
            return
        self.seen = path
        self.publish('', '', {})
        threading.Thread(target=self.read, args=(path,)).start()


class JoinEpisodes(object):
    """0.3.100 Skin settings > Details > Episodes in one file as one row (Skin.HasSetting(aeon.ep.join), off by default):
    when the Videos window opens a season (videodb://tvshows/titles/<show>/<season>/) that has episodes sharing one
    file, its list is replaced in place by the helper's (?info=episodes), where those episodes are one row. Replaced, so
    Back still goes to the seasons. Container.FolderPath / Content read no list item (guiread leaves them plain)."""

    def __init__(self):
        self.seen = None
        self.known = {}
        self.view = None                # (the helper's path, the view the season was shown in)

    def tick(self):
        if not xbmc.getCondVisibility('Skin.HasSetting(aeon.ep.join) + Window.IsActive(videos) + !Container.IsUpdating'):
            return
        path = xbmc.getInfoLabel('Container.FolderPath')
        if path == 'plugin://script.aeon.helper/':
            # Back from joined episodes opens the helper's (empty) top level: Kodi's parent of the list's address, the
            # season being gone from the history (replaced). Go on to where Back means: the seasons, or the shows.
            home = xbmcgui.Window(10000)
            parent = home.getProperty('aeon.ep.parent')
            if parent:
                home.clearProperty('aeon.ep.parent')
                xbmc.executebuiltin('Container.Update("%s",replace)' % parent)
            return
        if not xbmc.getCondVisibility('Container.Content(episodes)'):
            return
        if self.view and path == self.view[0]:
            # the season's own view (Kodi keeps a plugin list's view apart: it would open in another one); Kodi then
            # remembers it for the joined lists
            xbmc.executebuiltin('Container.SetViewMode(%s)' % self.view[1])
            self.view = None
        if path == self.seen:
            return
        self.seen = path
        key = multiep.season_path(path)
        if not key:
            return
        if key not in self.known:
            params = {'tvshowid': key[0], 'properties': ['file']}
            if key[1] >= 0:
                params['season'] = key[1]
            episodes = (rpc('VideoLibrary.GetEpisodes', params).get('result') or {}).get('episodes') or []
            if len(self.known) > 200:
                self.known.clear()
            self.known[key] = multiep.shared(episodes)
        if self.known[key]:
            target = 'plugin://script.aeon.helper/?info=episodes&tvshowid=%d&season=%d' % key
            view = xbmc.getInfoLabel('System.CurrentControlId')
            self.view = (target, view) if view.isdigit() and 50 <= int(view) < 10000 and view != '9000' else None
            xbmc.executebuiltin('Container.Update("%s",replace)' % target)
            xbmc.log('[script.aeon.helper] episodes of show %d season %d share files: one row each' % key, xbmc.LOGINFO)


STUDIO_SOURCES = (('aeon.studio', 'ListItem.Studio'), ('aeon.ss.studio', 'Container(9701).ListItem.Studio'))


def publish_studios(state):
    """The first studio of the item in focus (aeon.studio; the information page) and of the screensaver's slide
    (aeon.ss.studio), each with the full text it came from (<name>.of): the skin shows a logo only while that still
    matches, so a logo never belongs to the item before."""
    from resources.lib import studio
    home = xbmcgui.Window(10000)
    if 'studio_names' not in state:            # 0.3.92: the logos the studio pack has (read once)
        path = xbmcvfs.translatePath('special://home/addons/resource.images.studios.white/resources/Textures.xbt')
        try:
            state['studio_names'] = studio.xbt_names(path) if os.path.isfile(path) else None
        except Exception as error:             # an unreadable pack: the first studio, as before
            xbmc.log('[script.aeon.helper] studio logos: %s' % error, xbmc.LOGINFO)
            state['studio_names'] = None
    for prop, label in STUDIO_SOURCES:
        full = xbmc.getInfoLabel(label)
        if state.get(prop) == full:
            continue
        state[prop] = full
        logo, text = studio.pick(full, state['studio_names'])
        home.setProperty(prop, logo)
        home.setProperty(prop + '.text', text)
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


def migrate_fanblur():
    """0.3.111 (skin 0.56.45): Library fanart blur went from Off / Light / Medium / Strong to Off / -2 .. +2 (0 = the
    old Light, the default now): Skin settings' and every view's old value moves to the new step, once per start."""
    import json
    from resources.lib import blur
    try:
        res = json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'Settings.GetSkinSettings'})))
        moved = 0
        for item in res.get('result', {}).get('settings', []):
            sid, value = item.get('id', ''), item.get('value')
            if sid == 'aeon.x.fblur' or (sid.startswith('aeon.vo.') and sid.endswith('.fblur')):
                new = blur.fanblur_new(value, view=sid != 'aeon.x.fblur')
                if new is not None:
                    xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'Settings.SetSkinSettingValue',
                                                    'params': {'setting': sid, 'value': new}}))
                    moved += 1
        if moved:
            xbmc.log('[script.aeon.helper] Library fanart blur: %d old values moved to the new steps' % moved, xbmc.LOGINFO)
    except Exception as error:
        xbmc.log('[script.aeon.helper] fanart blur migration: %s' % error, xbmc.LOGINFO)


def splash_fanart():
    """0.3.108 (skin 0.56.42): the start-up splash shows a random film's (else show's) fanart from the library under its
    veil: Window(Home).Property(aeon.splash.fan). One library call each, in a thread, as the service starts."""
    for method, key in (('VideoLibrary.GetMovies', 'movies'), ('VideoLibrary.GetTVShows', 'tvshows')):
        try:
            got = rpc(method, {'properties': ['art'], 'sort': {'method': 'random'}, 'limits': {'start': 0, 'end': 5}}).get('result')
        except Exception:
            continue
        for item in (got or {}).get(key) or []:
            fan = (item.get('art') or {}).get('fanart')
            if fan:
                xbmcgui.Window(10000).setProperty('aeon.splash.fan', fan)
                return


def run():
    # 0.3.96: list labels and conditions are read on Kodi's main thread (guiread.py: a Kodi lock-order freeze)
    guiread.install()
    # one instance only: a newer start (add-on re-enabled / updated) takes over and this one ends
    token = str(time.time())
    xbmcgui.Window(10000).setProperty('aeon.helper.token', token)
    threading.Thread(target=splash_fanart).start()
    threading.Thread(target=migrate_fanblur).start()
    monitor = Monitor()
    manifest_check()
    migrate_settings()
    try:                         # Skin settings > Player > Save lyrics next to the song, as CU LRC Lyrics has it
        from resources.lib import lyricsave
        lyricsave.sync()
    except Exception as error:
        xbmc.log('[script.aeon.helper] lyrics save sync: %s' % error, xbmc.LOGINFO)
    try:                         # 0.3.102: Media info chips count again after new chips joined the picker ("7 / 17")
        from resources.lib import chips
        if xbmc.getInfoLabel('Skin.String(aeon.chips.shown)'):
            now = chips.shown(lambda flag: xbmc.getCondVisibility('Skin.HasSetting(%s)' % flag))
            if xbmc.getInfoLabel('Skin.String(aeon.chips.shown)') != chips.summary(now):
                xbmc.executebuiltin('Skin.SetString(aeon.chips.shown,%s)' % chips.summary(now))
    except Exception as error:
        xbmc.log('[script.aeon.helper] chips count: %s' % error, xbmc.LOGINFO)
    try:                         # 0.3.103 Skin style (skin 0.56.27): the library's glass follows the style
        from resources.lib import skinstyle
        call = skinstyle.builtin(xbmc.getInfoLabel('Skin.String(aeon.fgmenu)'), xbmc.getInfoLabel('Skin.String(aeon.fgmat)'))
        if call:
            xbmc.executebuiltin(call)
    except Exception as error:
        xbmc.log('[script.aeon.helper] skin style: %s' % error, xbmc.LOGINFO)
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
    sidecars = MediaInfoSidecar()
    player_sidecar = PlayerSidecar()
    focus_art = focusart.FocusArt()                # 0.3.108: the focused title's art at once in a big library
    set_row = setrow.SetRow()                      # 0.3.109: the spotlight's set strip path (a Kodi 22 freeze)
    join_episodes = JoinEpisodes()
    studios = {}
    memory = MemoryTrim()
    art_types = ArtTypeWatch()
    smooth_progress = smoothprog.SmoothProgress()   # Now playing: the fill glides (0.3.84)
    chapter_pictures = chapterwin.ChapterPictures()
    home_preload = HomePreload()
    start_item = StartItem()
    osd_album = OsdAlbum()
    sk_chapters = skchapters.SkippyChapters()
    fgs_facts = fgsfacts.Facts()
    round3_facts = round3.Facts()
    from resources.lib import tmweek            # 0.3.122: TV Timers as the week in lanes
    timers_week = tmweek.Week()
    from resources.lib import livetv            # 0.3.123: the guide's day strip
    guide_days = livetv.Days()
    palette = {}
    try:
        menufile.ensure_android()
    except Exception as error:               # never let a menu file stop the service
        xbmc.log('[script.aeon.helper] Power row: %s' % error, xbmc.LOGINFO)
    try:
        menufile.ensure_custom_nodes()       # custom items 4-10 (skin 0.54.0)
    except Exception as error:
        xbmc.log('[script.aeon.helper] custom item nodes: %s' % error, xbmc.LOGINFO)
    refresh_artists(monitor)
    refresh_videos(monitor)
    while not monitor.waitForAbort(POLL):
        if xbmcgui.Window(10000).getProperty('aeon.helper.token') != token:
            return
        guiread.tick()                           # 0.3.96: last tick's list labels in one main-thread call
        # 0.3.96: right after the batch, while its focused item is the newest the service has
        # the item the skin is showing: Home properties follow it (all ratings, not only the default one)
        key = (xbmc.getInfoLabel('ListItem.DBType'), xbmc.getInfoLabel('ListItem.DBID'))
        if key != seen:
            seen = key
            publish_ratings(fetch_ratings(rpc, *key))
            searchwin.publish_show(*key)              # Fused Glass Search window: "You're on S3 E1" (0.3.73)
            try:
                epcomb.publish_season(*key)           # Fused Glass season views: the next airing (0.3.115)
            except Exception as error:
                xbmc.log('[script.aeon.helper] season airing: %s' % error, xbmc.LOGINFO)
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
                xbmcgui.Window(10000).setProperty('aeon.epm.%d' % cid, fetch_epmark(rpc, *ckey, upcoming=nextaired.kept('episodes') if ckey[0] == 'episode' else None))
                if cid == 538:
                    epcomb.publish_focus(*ckey)
        publish_view_options(shown_options)
        themes.tick()
        sync_theme(palette)
        sync_palbase(palette)
        if xbmc.Player().isPlaying():                 # playing or paused: the Planner read waits for the quiet after it
            last_played = time.time()
        arrfeed.tick(palette, xbmc.Player().isPlaying())
        if time.time() - last_aired >= 60:            # looks every minute; reads only when the list is due and it is quiet
            last_aired = time.time()
            refresh_nextaired(monitor, last_played)
        trailers.tick()
        dolby.tick()
        sidecars.tick()
        player_sidecar.tick()
        focus_art.tick()
        set_row.tick(time.time())
        join_episodes.tick()
        publish_studios(studios)
        memory.tick()
        art_types.tick()
        smooth_progress.tick()
        chapter_pictures.tick()
        home_preload.tick()
        start_item.tick()
        osd_album.tick()
        sk_chapters.tick()
        try:
            fgs_facts.tick()
            round3_facts.tick()
            timers_week.tick()
            guide_days.tick()
        except Exception as error:
            xbmc.log('[script.aeon.helper] fgs facts: %s' % error, xbmc.LOGINFO)
        TIME_LEFT.tick()
        ADDON_ART.tick()
        MUSIC_BIO.tick()
        logocache.tick(palette)
        blurcache.tick(palette)
        blurcache.frost(palette)                 # 0.3.93: Menu theme Frost, the settings backdrop blurred
        searchhist.tick(palette)
        nextaired.publish_week(palette)
        nextaired.publish_next(palette)          # 0.3.94: the next episode of the show in an episode / season list
        nextaired.publish_season_pct(palette)    # 0.3.95: the share of watched episodes of an episode list
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


if __name__ == '__main__':
    run()
