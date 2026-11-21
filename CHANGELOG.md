# Aeon Fuse Helper changelog

The helper is released together with the skin. Each version below names the skin version it came with. The skin's
`CHANGELOG.md` tells the whole story of each feature. Versions not listed here have no note of their own there.

## 0.3.128

- Fusion TV guide: the current time pill above the yellow now dot. While the guide is open the helper publishes the
  half hour now runs in (`aeon.gd.half`, written like the guide's ruler labels), the minutes into it (`aeon.gd.min`)
  and the ruler label the pill would cover (`aeon.gd.hidelbl`). Skin 0.56.56.

## 0.3.127

- Start-up splash fanart only from G / PG rated films and shows (TV-G, TV-PG, TV-Y, UK U; "Rated PG", "US:PG" and the
  like); unrated or adult titles are never shown. None found: no fanart.
- One edition everywhere: the sidecar edition (aeon.mi.edition, aeon.pf.mi.edition) takes Kodi's own version name of
  the film when it has a real one ("50th Anniversary Edition"); the sidecar's edition (Curator wrote
  "Anniversary Edition") only when it has none. The list showed Kodi's name, the info page and the player the sidecar's.

## 0.3.126
- The Fuse menu theme is removed (skin 0.56.56): Skin style and the setup wizard no longer set it, and anyone on it
  goes back to the standard menus at start (one skin load, under the splash).

## 0.3.125
- Fonts after a skin update (skin 0.56.55): the skin reload that writes your fonts into the fresh Font.xml no longer
  ends the start-up splash (fontpick.sync sets aeon.splash.keep first).

## 0.3.124
- Recommended add-ons (skin 0.56.54): TinyPPI only on CoreELEC; elsewhere its row says "CoreELEC only", it is not
  counted in n / 15 and the setup wizard does not install it (recommended.fits).

## 0.3.123
- Live TV in the Fused Glass style (skin 0.56.53, canvas round 8), resources/lib/livetv.py: the guide's day strip
  (eight days, a dot where a timer is set, the day in view, the day in words for the programme's line) and the Timer
  rules cards (?info=timerrules: what each rule catches as a sentence; livetv,delrule deletes the focused rule).
- TV Timers: Kodi 22 has no timertype field (the timer list came back empty); reminders now count as their own kind.

## 0.3.122
- TV Timers as the week in lanes of time (skin 0.56.53, canvas round 7 idea B), resources/lib/tmweek.py: the next five
  days with up to three timers a day placed by their time, the hour span, the now mark, the header and the block of
  the focused row; RunScript(script.aeon.helper,tmweek,delete) deletes the focused timer after asking.

## 0.3.121
- The Sort and show only panel (skin 0.56.53, dialog 1179, Films in the Fused Glass style), resources/lib/sortshow.py:
  the sorts Kodi offers for films, OK again flips the order; filters (unwatched, in progress, watched, 4K, HDR, several
  versions, genre, decade, MPAA rating) joined into a smart-playlist path; counts per filter.
- Sort and show only for TV shows, albums and artists too; the colour picker's contrast numbers (Kodi 22 names the
  window dialogcolorpicker).
- The keyboard reads the typed text with Control.GetLabel(312).index(1) (the plain label is empty for an edit control).

## 0.3.120
- The keyboard in the Fused Glass style (skin 0.56.53): while it is open, the library films and shows whose title holds
  what is typed (aeon.kb.h1-3, aeon.kb.found); RunScript(script.aeon.helper,kbset,h1|s1) types a match or a recent
  search into the field.

## 0.3.119
- Files in the Fused Glass style (skin 0.56.53): the path of Videos / Music Files (list 50) as crumbs (aeon.f50.c1-4) and a
  peek inside the folder in focus.

## 0.3.118
- Round-3 Fused Glass style windows (skin 0.56.53), resources/lib/round3.py: the file browser's path as crumbs, a peek
  inside the folder in focus (file browser, media source), the text viewer's reading time, plugin lists ?info=peek /
  sources / substreams (the playing video's subtitles, your language first), RunScript(...,setsub,<index>|off).

## 0.3.117
- Fused Glass style windows (skin 0.56.53), resources/lib/fgsfacts.py: the colour picker's contrast (on white, on the
  dark ground), the OSD offset's place on a +-0.5 s ruler, an album's tracks as ranges for the Music information bar,
  the intermission's mark from Skippy's chapters sidecar (read only), and plugin ?info=picstrip (Picture info's strip
  of the folder).

## 0.3.116
- Music information in the Fused Glass style (skin 0.56.53): plugin ?info=albums lists an artist's other albums (oldest
  first); ?info=albums / similar / toptracks also take albumid= and read the album's first artist.

## 0.3.115
- Fused Glass season views (skin 0.56.53): the service publishes aeon.sn.next ("S3 E7 airs Wednesday 25 November") and aeon.sn.dbid for the season in focus (epcomb.publish_season).
- addonart: aeon.ab.repofanart, the fanart of the repository being browsed (the add-on browser shows it where the item in
  focus has none).
- Recommended add-ons: the Aeon Fuse Waveform Visualizer build for this device (recommended.waveform_id: aarch64 ->
  linux-arm64, armv7 -> linux-armv7, x86_64 -> linux-x86_64, 64-bit Windows -> windows-x64; none on Android / macOS),
  from the Skippy Repo, after the Aeon Fuse Screensaver.
- swap.py delete,<position>: deletes a custom Home menu item (homemenu.remove moves the ones below up; its skin
  strings and its aeonmenu2 entry are cleared, menufile.clear_custom).
- swap.py theme: the skin's aeon.fglass / aeon.vglass are set before Kodi's Theme changes, so the reload Kodi does
  draws the new theme at once (it showed the old one for a moment, then the service loaded the skin again).
- episodes.fetch_epmark: no season finale for the last episode of a season in the library while the next-aired list
  has a later episode of that season (The Rings of Power S3 E6, E7 airing 25 November).

## 0.3.114 (skin 0.56.53)
- service PlayerSidecar: the playing video's Dolby Vision profile (aeon.pf.dvp) and mediainfo sidecar (aeon.pf.mi.*)
  for the player's information page.
- timeleft: aeon.left.<k>.hmb, "[B]3[/B]·29 left" for the library rows (was "209 min left").
- mediainfo.container_name: one short container name everywhere (MKV, MP4, M2TS ...); a Curator sidecar's "Matroska"
  came through as MATROSKA while tinyMediaManager's was mapped to MKV.
- service MediaInfoSidecar: on Home, the sidecar of the spotlight's film / episode (lists 9441, 9421-9423) when the
  focused item is no video, so the spotlight's sidecar chips have their values.
- wizard.DEFAULTS: Aeon and Aeon Glass take aeon.vbg = color (Color backdrop) and aeon.boxbg = '' (Colors corner
  boxes); tests/test_wizard.py checks it.
- addonrec.py + resources/lib/recommended.py: RunScript(script.aeon.helper,addonrec) lists the recommended add-ons and
  installs the one picked (its repository zip first when needed, after a yes); addonrec,count writes
  Skin.String(aeon.rec.count); addonrec,batch installs the add-ons ticked in the setup wizard (skin bools
  aeon.wiz.add.<id>, cleared) without asking again. tests/test_recommended.py.
- remotelib.py + resources/lib/libremote.py: RunScript(script.aeon.helper,lib,update|clean,video|music) runs the
  library update / clean here or sends it to another Kodi's JSON-RPC (HTTP basic login); libremote,address|user|
  password|test are the settings rows. The password is the hidden setting libremote_pass. context.py's Update / Clean
  library go through it too. tests/test_libremote.py (a fake Kodi web server).

## 0.3.113 (skin 0.56.52)
- placepick.py + resources/lib/places.py: RunScript(script.aeon.helper,placepick,rate|chip) opens the "Ratings shown
  in" / "Media info shown in" multi-select of the places (Library views, Information pages, Widget & Spotlight
  screens, Home spotlights, Player info, Screensaver, Live TV); an unticked place sets aeon.<kind>off.<place>, the row
  value is Skin.String(aeon.<kind>.places). tests/test_places.py.

## 0.3.112 (skin 0.56.49)
- resources/lib/skchapters.py + service tick: Skippy's segments (Window(Home) skippy.parse_cache_snapshot.v1, checked
  against the playing file) as chapters: aeon.sk.ranges in Player.Chapters form, aeon.sk.part, aeon.sk.count; cuts
  closer than 0.75 % of the length count once; cleared when no video plays. tests/test_skchapters.py.

## 0.3.111 (skin 0.56.45)
- service.HomePreload: waits for every Home row, also one the skin armed first, and marks each (aeon.pl.<sec>.in) for
  the splash; an empty row counts after 4 s quiet (was 1.5 s).
- Library fanart blur: Off / -2 .. +2 (radii -, 1, 2, 4, 9, 16; '' = 0); old values move once per start
  (migrate_fanblur). View options pshadow / pop / pblur / ptint; Panel blur per view (blurcache.tick).
- startitem (Skin settings > Home menu > Start on) and service.StartItem.
- osdalbums: the album track list in the music player controls (osdalbum prev|next, osdplay <songid>, OsdAlbum).
- skinstyle accepts dark for the Dark style (Skin settings' choose mode).

## 0.3.110 (skin 0.56.44)
- blurcache.frost: also Aeon Glass's Panel blur (Skin.String(aeon.agblur) light / medium / strong, radius 6 / 14 / 24):
  the menus' backdrop blurred, as for Fused Glass's Frost style. blur.menu_radius (tests).
- wizard: "Use the defaults" resets aeon.agfocus and aeon.agblur too.

## 0.3.109 (skin 0.56.43)
- picshow: the slideshow of the newest picture folder starts from the Pictures window (opened first, loaded), not over
  Home: SlideShow() over Home froze Kodi 22 (see the skin's 0.56.43 note).
- setrow.py: the Home spotlight's set strip path worked out over JSON-RPC and written to Skin.String(aeon.rt.setrow) when
  another set comes up; backup.py leaves aeon.rt.* out of Export / Import.

## 0.3.108 (skin 0.56.42)
- settings,export / settings,import (settingsio.py, resources/lib/backup.py + tests/test_backup.py): Skin settings >
  System > Export / Import skin settings over JSON-RPC Settings.GetSkinSettings / SetSkinSettingValue (the Skin builtin
  when Kodi refuses one), Kodi's theme / colours / font, fonts written again when a font choice changed, RestartApp on Linux.
- focusart.py (+ tests/test_focusart.py): the focused library item's art from the library in a worker thread (newest
  focus wins), published as aeon.fart.* with aeon.fart.type / dbid, for big libraries whose list art loads from the top.
- npartist: the strip's Now playing panel opens the playing song's artist in the music library.
- View options fop / fblur / ftint (per library view); the blurred library fanart follows the view's Fanart blur.
- The start-up splash's backdrop: a random film's (else show's) fanart as aeon.splash.fan when the service starts.
- Wizard defaults: aeon.homegrad, aeon.fgnpleft.

## 0.3.107 (skin 0.56.40)
- Setup wizard: wizard,open publishes what waits for Finish (aeon.wiz.theme fused / aeon / glass, menutheme, fgmenu,
  palette with pal0 and palidx, font) and opens it at step 1; wizard,defaults[,finish] applies the chosen theme's
  defaults (resources/lib/wizard.DEFAULTS, a placeholder table until the user's own); wizard (Finish) applies Skin
  style, palette, theme (three themes now) and fonts, then restarts Kodi on Linux or reloads the skin elsewhere (also
  for a new focus highlight, aeon.wiz.reload). wizard,palette (a palette in Kodi's list) is kept for the parked
  Skin-settings-look wizard. wizard.plan takes the wanted and the running state.
- fonts,set,<preset> and fonts,wizard: the font choice without the skin reload; Font.xml is written at Finish
  (fontpick.apply).
- Tests: plan for style, palette and theme; defaults cover every setting the wizard changes; palette pictures.

## 0.3.106 (skin 0.56.31)
- fonts.build writes uppercase twins uc_st_<name> of the settings fonts in CAPS (ui_24, ui_24_semibold, ui_24_bold,
  ui_22_semibold, ui_22_bold, small_20_semibold): the settings face with style uppercase, in every font set, for the Fused Glass style's capitals.
  New fonts.uppercase(rest). Tests: twins follow the settings face, are rebuilt not doubled, keep an own style.

## 0.3.105 (skin 0.56.29)
- RunScript(script.aeon.helper,skinstyle): Skin settings > Appearance > Skin style in Fused Glass steps Dark -> Clear ->
  Frost -> Fused Glass -> Dark (aeon.fgmenu '' / glass / frost / system), puts the library glass in step, and offers to
  start Kodi again going to or from Fused Glass (resources/lib/skinstyle.py next_style / needs_restart).

## 0.3.104 (skin 0.56.28)
- Expert settings > Panel blur (Skin.String(aeon.x.pblur): Off / Light / Default / Strong): the radius of the blurred
  copy under the Fused Glass panels (8 / 14 / 22 at 640 x 360; Off publishes none). Copies at other radii get their own
  cache names (<md5>_r<radius>.jpg); the default keeps the old ones.
- Expert settings > Fanart blur (aeon.x.fblur: Off / Light / Medium / Strong): a blurred copy of the library views'
  fanart ($VAR[Aeon_V_Fan]) in Window(Home).Property(aeon.fanblur), radius 4 / 9 / 16; the copy before stays until the
  next is ready; Off clears it (blurcache.fantick).

## 0.3.103 (skin 0.56.27)
- Skin style: at start the library's glass (Skin.String(aeon.fgmat)) is put in step with the Fused Glass Skin style
  (aeon.fgmenu: Dark -> none, Clear -> clear, Frost -> frost), now that the Library view theme row is gone
  (resources/lib/skinstyle.py; an old Raised setting goes with it).

## 0.3.102 (skin 0.56.26)
- Media info from sidecars: aeon.mi.format (Curator's <source_format>, else the source guessed from the release
  name), aeon.mi.vsource (Curator's <video_source>) and aeon.mi.vcodec (<video_codec>, tinyMediaManager's video
  Format) for their own chips. aeon.mi.source keeps the combined value for the information page's card line.
- Media info chips picker: Video source, Video codec and Version (the sidecar's <edition>) join it, off by default
  (aeon.chip.vsource / vcodec / edition); 17 chips. The service recounts Skin.String(aeon.chips.shown) at start so a
  count saved as "N / 14" reads "N / 17".

## 0.3.101 (skin 0.56.24)
- Joined episode lists (?info=episodes): each row carries its show's certificate, genres and studio, as a library
  episode does, and the library's label ("01. LA X (1)", a joined row "01-02. LA X"; label mask %L); multiep.label.

## 0.3.100 (skin 0.56.23)
- Episodes in one file as one row: plugin://script.aeon.helper/?info=episodes&tvshowid=&season= lists a season with
  the episodes of one file joined (resources/lib/multiep.py: range, title, plot, the file's own duration, the episode
  code in the user's form; tests/test_multiep.py); the service (JoinEpisodes) opens it in place of a season that has
  such files while Skin.HasSetting(aeon.ep.join) is on (Container.Update ..., replace), in the view the season was
  shown in (Kodi keeps a plugin list's view apart); Back goes to the show's seasons (or the shows, for a show with one
  season) instead of the helper's empty top level. The rows' label is the plain title.

## 0.3.99 (skin 0.56.22)
- Screensaver rounds: plugin://script.aeon.helper/?info=ssround&n=&kinds=&r= returns N items drawn at random from the
  sources asked for (films, shows, albums from the library; in the cinemas now; airing today / tomorrow), mixed
  (resources/lib/ssround.py, never the same source twice in a row while another has items), each with property
  aeon.ss.kind; sets aeon.ss.pages / aeon.ss.ready. Library films now carry their directors. Tests: test_ssround.py.
- Skin settings > Details > Media info chips: RunScript(script.aeon.helper,chippick) (chippick.py,
  resources/lib/chips.py, tests/test_chips.py).
- Home > Pictures' default icon is the camera (menuicons).
- The Pictures slideshow command imported xbmc / xbmcgui under the names swap.py's main() makes local (it failed with
  UnboundLocalError in 0.3.98 on the first try; fixed before release).

## 0.3.98 (skin 0.56.21)
- Home > Pictures: plugin://script.aeon.helper/?info=picfolders walks the picture sources (resources/lib/picfolders.py:
  folders a few levels deep that hold photos or videos, newest first, counts, file dates, newest photos; limited to
  400 folders / 20 seconds, kept 15 minutes in picfolders.json) and sets the Home window's aeon.pic.* properties;
  ?info=picopen opens a folder in the Pictures window; RunScript(script.aeon.helper,picshow) plays the newest folder
  as a slideshow. Tests: tests/test_picfolders.py.

## 0.3.97 (skin 0.56.20)
- Mediainfo sidecars (Skin settings > Details > Media info from sidecars, off by default): for the film / episode in
  focus the service reads <name>.cmm_mediainfo.xml (Curator Media Manager, first) or <name>-mediainfo.xml
  (tinyMediaManager) once, in a thread, and publishes aeon.mi.* (source such as UHD Remux / Blu-ray / WEB-DL / DVD,
  edition, video, HDR, bitrate, size, the main audio track, audio / commentary / subtitle counts, subtitle languages,
  SDH, chapters) with aeon.mi.path, the file they belong to (`resources/lib/mediainfo.py`, tests/test_mediainfo.py).
  tinyMediaManager's file has no source field: the source and edition come from the release name.
- Planner: a list kept from before 0.3.97 (rebuilt every two weeks by default) shows the series and season premieres
  at once, from the season and episode numbers; finales come with the next rebuild.
- In cinemas now can keep only films made in the United States or one more country (Skin.String(aeon.cinema.country),
  picked with RunScript(script.aeon.helper,cinemacountry)): TMDb's discover over the same weeks with
  with_origin_country, since TMDb Helper sends its own region with every request (online.origin_of, tests).
- Home preload: Window(Home) aeon.pl.done once the strips under Movies, TV shows and Music are in (the skin's
  start-up splash waits for it).

## 0.3.96 (skin 0.56.16)
- Fix: Kodi could freeze for good when a long library list was rebuilt (closing a film's information window after
  adding a version, a refresh) while the service read a list label. Kodi held the list's lock and waited for the GUI
  lock; the service held the GUI lock and waited for the list's lock. Every label or condition that names a ListItem or
  a Container is now read over JSON-RPC, which Kodi answers on its main thread; skin variables ($VAR) are worked out
  from the skin's definitions the same way in media windows (`guiread.py`). The labels of the last tick come in one
  call per tick.

## 0.3.95 (skin 0.56.15)
- `aeon.left.<k>.hhmm`: the time left as "0:07 left" (skin string 32606), written after ENDS in the Aeon info bands.
- `aeon.cont.pct` / `aeon.cont.path`: the share of watched episodes of the episode list on screen (Kodi's
  Container.TotalWatched / TotalUnWatched), for the season ring on the Aeon Compact list's poster.

## 0.3.94 (skin 0.56.14)
- Next episode of the show in an episode / season list: `aeon.next.of` (the show), `aeon.next.code` ("S3 E5"),
  `aeon.next.day` ("Wed 18 Nov") from the Planner's list.
- `aeon.tc.focus` (the focused album's track count) also for the Album wall, Cover showcase and Artist wall.

## 0.3.93 (skin 0.56.12)
- Add-on browser: up to 20 screenshots (`aeon.ab.shot1` .. `aeon.ab.shot20`).
- Menu theme Frost: `aeon.bgfan.blur`, a blurred copy of the settings backdrop `aeon.bgfan` (the blur cache), with
  `aeon.bgfan.blursrc` = the backdrop it was made from.

## 0.3.92 (skin 0.56.11)
- Studio logo: `aeon.studio` is the first of the item's studios that has a logo in resource.images.studios.white (its
  Textures.xbt index read once); none: `aeon.studio` empty and `aeon.studio.text` = the first studio's name.
- `musicbio.py`: `aeon.m.bio` for albums without a review (the artist's bio, `aeon.m.bio.album`) and song lists (the
  album's review or the artist's bio, `aeon.m.bio.path`).

## 0.3.91 (skin 0.56.10)
- `addonart.py`: the settings dialog's fanart is a blurred copy (the blur cache of the Fused Glass backdrops).

## 0.3.90 (skin 0.56.9)
- `addonart.py`: the screenshots of the add-on in focus in the add-on browser (`aeon.ab.path`, `aeon.ab.shot1`-6,
  `aeon.ab.shots`) from its addon.xml or Kodi's add-on database (that repository's version), and the fanart of the
  add-on whose settings are open (`aeon.as.fanart`, found by the name in the dialog's heading).

## 0.3.89 (skin 0.56.8)
- `timeleft.py`: the time left of every film, episode and music video in progress for the list rows
  (Window(Home) `aeon.left.<k>.type` / `.id` / `.text`, k = 1..40, the most recently played first; skin string
  32512 "{n} min left"). Refreshed at start, after playback stops and when the video library changes.
- Track counts for the Album list (532): `aeon.tc532.<row>` for its ten screen rows, and `aeon.tc.focus`.

## 0.3.88 (skin 0.56.4)
- Home strips load ahead: the service (`HomePreload`) sets Window(Home) `aeon.pl.movies`, `aeon.pl.tv` and
  `aeon.pl.music` one after another after Kodi starts, each when the last strip is in, only while Home is open and no
  video plays. The skin keeps a loaded strip's titles.
- `swap.py focusstrip`: Down on Movies / TV / Music waits up to 45 s while the strip is still loading or refreshing
  (was 5 s), lands once it has titles and is done, and stops once it finished empty. The service waits while a
  dialog has the focus (CoreELEC's release notes over Home).

## 0.3.87 (skin 0.55.2)
- `swap.py epgreload`: EPG tools > Reload EPG. Restarts the enabled PVR client add-ons and reopens the channel that
  was playing.

## 0.3.86 (skin 0.54.0)
- Home menu: 24 positions and 10 custom items (`resources/lib/homemenu.py`: rows, custom numbers, where Add item
  goes; tests/test_homemenu.py). `swap.py add` opens the type picker headed Add item for the first free position
  after the last item (a gap when the end is full; all 24 in use: it says so) and focuses the new row once Kodi shows
  it. `swap.py count` sets Window(Home).Property(aeon.menucount), the positions in use (Skin settings runs it on
  open; Choose type, Add item and Restore default order update it). Choose type set to Empty on the last item moves
  the focus to Add item, since that row hides. Restore default order empties positions 14-24 too. Custom item numbers
  are read whole (custom10), not by their last digit.
- Spotlight lists and headings for custom items 4-10 (boxart.SPOT_LISTS, service.SPOT_SECTIONS).
- `menufile.ensure_custom_nodes()` at service start: a saved skinvariables aeonmenu2 file from before skin 0.54.0
  gets empty entries for custom items 4-10 (guid-aeon0015 to 0021), so their widgets and submenus can be edited.

## 0.3.85 (skin 0.52.3)
- Smooth song progress: on unless Skin.HasSetting(aeon.smoothprogress.off), and at the rate of
  Skin.String(aeon.smoothprogress.rate): Screen ('', System.FPS read every quarter second, the screen mode's refresh
  rate when that gives no number, within 10-120) or 10 / 25 / 30 / 60. Updates keep to a steady clock (each one due
  1 / rate after the last), so the time the calls take does not slow the rate. The pixel pacing of 0.3.84 is gone.
  The log line names the last rate.

## 0.3.84 (skin 0.52.1)
- Smooth song progress (`smoothprog.py`): while the Fused Glass Now playing window is up and the skin setting is on,
  a short-lived thread (aeon-smoothprog) sets the card's progress 4801 with `ControlProgress.setPercent` from
  `xbmc.Player().getTime()`, which on the box moves in 10 ms steps and stays within 7 ms of a steady clock, so it is
  read for every update instead of being interpolated. About twice per screen pixel of travel, 4 to 60 times a
  second; it never steps back by less than half a second (Kodi's time wobbles a few milliseconds while paused). The
  control is looked up for every update, since a skin reload rebuilds it. One log line per Now playing visit.

## 0.3.83 (skin 0.52.0)
- The show progress for the Showcase of seasons (aeon.sp.*, 0.3.81) is gone: the pill now shows the season in focus,
  which Kodi gives the skin directly.

## 0.3.82 (skin 0.51.0)
- Backdrop = Colors and the box colours take the item in focus of a view's second list (System.CurrentControlId,
  when that container holds library items). In a library window ListItem always means the view's own list, so the
  episodes of Combined and the Season list kept their season's colour.

## 0.3.81 (skin 0.50.1)
- Seasons listings: the show's title and its watched / total episodes and percent are published as aeon.sp.title /
  watched / total / pct, with aeon.sp.of naming the folder they belong to (the Fused Glass Showcase of seasons).

## 0.3.80 (skin 0.49.0)
- Artist rows: the album count is published for ten screen rows (aeon.ac.0-9; the Fused Glass Rows view shows ten).

## 0.3.79 (skin 0.47.0)
- View settings: the helper also publishes the Fused Glass library views' per-view options Progress rings
  (aeon.vo.rings) and Logos instead of titles (aeon.vo.logos), like Watched status (VIEW_OPTIONS in service.py).

## 0.3.78 (skin 0.46.3)
- plannerwin, Earlier days: the days before today hold only the library's aired episodes (planner.earlier_mix), the
  same as their lists; the kept list's older entries no longer make Left / Right stop on a day whose list is empty.
  The commands Shows you watch, Show and Update now count the earlier days as well (they used today as the first day).
- plannerwin, focus: a focused list about to get other items hands the focus to the holding button (9501 Day, 9518
  Week) before the new day is published; then settle() waits for Container(id).IsUpdating to end and the focus goes to
  the list when it has items, else to the holding button. Never SetFocus on an empty list (that drops the focus), and
  the focus is not taken back from where the user moved meanwhile.
- plannerwin: aeon.planner.busy while the lists are filled (init, view, weekstart, watching, past, what, update; the run
  that sets it clears it once the selected list has loaded).
- plannerwin.aired: the week's aired episodes cached for ten minutes in Home property aeon.planner.aired (key: week,
  today, aeon.count.episodes; planner.aired_cache_key / aired_cached); plugin ?info=planner reads a past day from it
  (plannerwin.aired_on), or asks the library for that one day when there is no copy yet.
- tests: test_earlier_mix, test_aired_cache (test_planner_fused.py).

## 0.3.77 (skin 0.45.2)
- plugin ?info=recentsets[&limit=N] (default 20, at most 100): the movie sets whose films were played last, newest
  first, as library set folders (videodb://movies/sets/<id>/, DBType set + DBID for the spotlight's film strip, the
  set's art and plot, lastplayed = the set's film played last). One Files.GetDirectory call on Kodi's own Sets list
  sorted by last played (it already leaves out one-film sets when the library setting says so); sets nobody played
  are dropped. Logic in resources/lib/recentsets.py with tests (tests/test_recentsets.py). About 1 s on the PC library
  (507 sets): asking each set's details instead cost 0.35 s per set there.

## 0.3.76 (skin 0.45.1)
- Favourites: an episode saved as a file is found in the library (its thumb as the tile and under the show's logo,
  Continue / Resume / from the start, All episodes, the next airing; Kodi's information for it); a TV channel favourite
  shows the channel's logo (tile and spotlight) and Now / Next / the plot.
- plannerwin: dayname / daydate, wfirst / wflip (no slide between days of the same week), pastname and the command
  past (Earlier days); aired episodes of this week's earlier days from the library.
- plugin ?info=planner: earlier days of this week (Earlier days on), one GetTVShows query per day for Shows you watch
  and "You're on"; ss=1 dresses the items for the screensaver (the show's poster, backdrop and logo, the show's name
  as title, aeon.ss.line1 "S3 E5 - title", aeon.ss.line2 the network).
- service: the KarmaMole colour wash follows the title in focus in the Planner; the Episode combined view (538) is
  watched for its episode marks.
- lyricsave.py: the command lyricsave switches CU LRC Lyrics' save_lyrics2_lrc / _txt; at start-up the skin setting
  aeon.lyrics.save is set as the lyrics add-on has it.

## 0.3.75 (skin 0.44.0)
- epcomb.py: plugin ?info=seasons&path=<folder> (the Episode combined view's season pills; also sets aeon.ec.stats and
  aeon.ec.next for the season on screen) and, from the service, aeon.ec.left / aeon.ec.resume for the episode in focus
  of list 538 (also added to the containers whose episode mark is published: aeon.epm.538).

## 0.3.74 (skin 0.43.0)
- plannerwin: commands watching (Shows you watch) and bg (Colors / Neutral / Fanart), Week starts Today, properties
  headline, watching, watchname, bgname, summary and per day day / short.
- plugin ?info=planner: Shows you watch filter and "You're on S3 E1" (aeon.pl.on) for library shows you are behind on,
  with one query for the shows of the day.
- service: KarmaMole's list for the Fused Planner (Colors); blurcache also follows the Planner.
- resources/lib/planner.py: only_watched, behind, week_summary (tests: test_planner_fused).

## 0.3.73 (skin 0.42.0)
- service: aeon.boxuptime (how long the machine has been on), aeon.health / aeon.mem.pct / aeon.mem.text / aeon.cpu.pct
  (every 2 s), aeon.sys.major / tag / osname / osline / device / screen (every 30 s, Busy labels asked again) and
  aeon.countg.* (library counts with the language's thousands separator) for Fused Home > System
  (resources/lib/uptime.py, resources/lib/sysinfo.py).
- plugin ?info=favourites: Channels group (kind=channels; chan=0 keeps channels out of Video / Music), and for Fused
  Home > Favourites the tile shape, art or glyph, channel number and what is on, and the spotlight: next episode to
  continue, minutes left, resume point, next airing, episodes waiting, button labels and actions (resources/lib/favspot.py).
  New routes ?info=favplay (resume / start / play / shuffle) and ?info=favinfo (Kodi's information dialog).
- searchwin.py: the Fused Search window's keys (RunScript ...,searchkey,del|space|clear|kodi), the focused show's
  You're on S3 E1 / next airing (aeon.show.on / aeon.show.next) and plugin ?info=searchlib (library shows / films by title
  or cast). searchhist records the Fused window's query when it closes; search,N opens it with that query.
- Tests: test_sysinfo, test_favspot, Channels group in test_favourites.

## 0.3.72 (skin 0.41.0)
- logocache: also trims the clearlogo of the video playing and publishes it as aeon.osd.logo / aeon.osd.logo.src (the
  Fused player's Now playing pill).
- playerfacts.py (RunScript ...,playerfacts, run by the Fused information screen): subtitle and audio languages (counted),
  track counts, file name and size, and the season path of a library episode (aeon.pf.*).
- plugin ?info=playercast: the cast of the video playing (name, character, photo only when the library holds a real
  path; bare file names such as Morfydd_Clark.jpg are left out so the skin shows its own disc).

## 0.3.71 (skin 0.40.4)
- palette.py: after a palette other than Aeon, asks where it applies (menus and library views / menus only / library
  views only) and sets the matching colour file; `palscope` asks only that. resources/lib/palscope.py (tests) splits and
  builds the file names; the picker and the wizard leave the "(menus)" / "(library)" files out of their lists.
- service: Skin.String(aeon.palbase) = the palette's name without its scope, for the skin's label; per-view Corner
  boxes (aeon.vo.boxbg) published with the other View settings.

## 0.3.70 (skin 0.40.0)
- swap.py menutheme: values '' (Bridge / Glass's own menus), mosaic, ledger, tabslab, fused. Left / Right on the row
  step through them, OK steps to the next one in the Aeon theme (toggles Fuse in Glass); only a change to or from Fuse
  asks to restart Kodi (or reloads the skin).

## 0.3.69 (skin 0.39.16)
- planner.text_or_empty / real_episode_title (tests): placeholder plots ("None", "TBA" ...) become '' (the show's plot
  is used then); ListItem.Property(aeon.eptitle) = the episode's title unless it is generic ("Episode 2", "Folge 2",
  "#2"), for the spotlight's "Season 2 · Episode 2 · <title>".

## 0.3.68 (skin 0.39.15)
- artguard: a season's picture of the wrong shape with nothing in the folder that fits -> the slot is emptied
  (SetSeasonDetails art: null; the skin falls back to the show's picture, media managers fill empty slots). The summary
  says it was the library, not the files (32451), and lists emptied slots apart (32450).

## 0.3.67 (skin 0.39.14)
- artguard: show_art fallback for seasons (the show's picture). Replaced by emptying the slot in 0.3.68.

## 0.3.66 (skin 0.39.13)
- `artguard.py` + `resources/lib/artshape.py` (tests/test_artshape.py): art with the wrong shape. Shapes per type
  (poster / key art 0.4-0.9 width/height, banner 2.5-12, landscape / fanart 1.2-2.6); sizes from Kodi's texture cache
  (Textures.GetTextures), else Pillow on the start of the file. Service Monitor.onNotification(VideoLibrary.OnUpdate)
  -> Guard: films / shows (with their seasons) checked 4 s after the last update; RunScript(...,artcheck) = the whole
  library from the texture cache (video sources only: music covers are square folder.jpg pictures).
- options.py removed (the "More options" list): the skin had no way to open it any more; every one of its options
  has its own row in a Skin settings category. RunScript(script.aeon.helper,options) is gone with it.

## 0.3.65 (skin 0.39.11)
- `ArtTypeWatch` (service): while the information page's art-type list (Choose art) is open, a short-lived thread
  follows its focused type every 50 ms into Window(Home) aeon.arttype for the image picker's heading. DialogSelect's
  own unload actions cannot catch it: Kodi empties the list before they run.

## 0.3.64 (skin 0.39.10)
- `trailer.play` remembers whose trailer it is (show / film: kind, name, clearlogo, poster, read while the page is
  open) and, once the trailer itself plays (not the video that played before it), the playing file: Window(Home)
  aeon.tr.kind / title / logo / poster / now for the player overlays.

## 0.3.63 (skin 0.39.9)
- `trailer play <path>` (swap.py -> trailer.play): the information page's Trailer button. Closes the page, plays the
  trailer, and brings full-screen video to the front once it runs (a slow YouTube trailer played behind the page).

## 0.3.62 (skin 0.39.8)
- `check_osd_poster` (service): Window(Home).Property(aeon.osd.noseasonposter) = 1 while the playing episode's season
  poster is wider than tall (measured once per picture with Pillow); the player overlays then show the show's poster.

## 0.3.61 (skin 0.39.6)
- Home heading of a custom item's spotlight (`custom_head`): the sort's phrase with the item's name in bold,
  "Random **Sets**", from the skin's templates 32433-32439; a spotlight label that is just the item's name no
  longer replaces it.

## 0.3.60 (skin 0.39.6)
- `epggroup` (swap.py): EPG tools > Channel group closes the tools card at once, opens Kodi's group list on the
  guide and, when a new group was chosen and has loaded, goes to its first channel with the focus on the grid.

## 0.3.59 (skin 0.39.2)
- Home > Planner week strip: `planner.week_kinds` counts each day's episodes, films and albums apart;
  `nextaired.publish_week` adds aeon.plw.N.eps / .films / .albums / .iso. `plannerwin` init opens the day in
  aeon.planner.open (set by a day of the strip) in the Day view, without changing the saved view.

## 0.3.58 (skin 0.39.0)
- Planner day lists mark what is in the library already: `resources/lib/inlibrary.py` (Lookup: one TV show list and
  one episode list per show per list, films by title within a year, albums by title and artist) sets
  ListItem.Property(aeon.inlib) in `plugin.planner_item`. Tests: `tests/test_inlibrary.py`.

## 0.3.57 (skin 0.38.0)
- `fonts.py`: 14 more combinations (19 in all), 11 one-weight heading faces and 8 four-weight text families; a family can
  name its four files (Regular, Medium, SemiBold, Bold) when the files are named otherwise or a weight is missing
  (`weight_file`). The picker window has a preview slot for each family (45).

## 0.3.56 (skin 0.37.0)
- Font combinations (`resources/lib/fonts.py` PRESETS, `preset_choices`, `preset_of`): RunScript(script.aeon.helper,fonts)
  opens the combination picker first; its rows carry h / b preview numbers so the mock-up draws the title in the
  heading font and the rest in the text font. Four one-weight heading faces added after the older families (their
  preview numbers do not move). Skin strings from 32000 up are read through `$ADDON`.

## 0.3.55 (skin 0.35.0)
- Backdrop = Colors takes its colour from the picture on screen again (`boxart.art_keys(dbtype)`); 0.3.54's fanart-first
  wash gave an artist with a black-and-white photo a maroon page.
- Dolby Vision profiles (`resources/lib/dvprofile.py`): P5, P7 FEL / MEL / P7, P8.1 / 8.2 / 8.4, P10 from `<hdrdetail>`
  and from `.cmm_mediainfo.xml` (`dovi_profile`, `dovi_el_type`, `dovi_bl_compat`), checked against the box's files.

## 0.3.54 (skin 0.34.0)
- Backdrop = Colors: the page colour and soft wash come from the focused item's fanart (`boxart.art_keys(dbtype,
  wash=True)`: fanart keys first, poster keys after); the boxes follow the poster as before while no page uses Colors.
- Album track counts for the music Fanart list (`counts.album_tracks`, `publish_track_counts`): the albums on screen
  (`aeon.tc.0..4`) and the focused one (`aeon.tc.focus`); one song count per album (limits.total), kept.
- Home spotlight logo check (`publish_spot_logo`): the clearlogo of the item on screen is looked for once (in a
  thread); a missing file is published as `aeon.sp2.nologo` so the skin shows the title.

## 0.3.53 (skin 0.33.0)
- Planner sources (`arrfeed.py`, `resources/lib/arr.py`, tests/test_arr.py): the add-on has settings now (Planner
  sources: address and API key of Radarr, Sonarr and Lidarr, days ahead, Read now). Each calendar is read every three
  hours while nothing plays (`/api/v3/calendar` of Radarr and Sonarr, `/api/v1/calendar` of Lidarr); the key goes only
  in the X-Api-Key header to the address entered, and only the pictures' remote addresses are kept (a local one would
  carry the key). Wanted titles (monitored, not downloaded) are kept in `arr.json`; a source that cannot be reached
  keeps what it gave last. `nextaired.kept()` adds them to the Planner's own list (an episode once; a film in both as
  the app's entry), used by the Planner window, the Home Planner list and This week. Planner items of a source carry
  `aeon.source`, `aeon.release` (cinema, cinemanow, digital, physical, episode, newshow, album) and `aeon.releasetext`;
  albums `aeon.artist`. `aeon.arr.summary` (Radarr 12 · Sonarr 30) for the Planner's options row. New texts
  32030-32047 in all 22 languages.

## 0.3.52 (skin 0.32.0)
- Home header: `aeon.head.sp2` / `aeon.head.cat`, the spotlight's and the strip's category with the last word in bold
  (`resources/lib/headline.py`, tests/test_headline.py).
- Settings backdrop: a pool of fanart seen on Home plus a few random library titles; each time another window opens,
  `aeon.bgfan` gets a random one (`resources/lib/backdrops.py`, tests/test_backdrops.py).
- Favourites: `?info=favourites&kind=all|video|music|addons` lists Kodi's favourites of one group with the library
  artwork and plot of the show, film, set, album or artist they point at; `?info=runfav&n=<i>` opens one as Kodi's
  Favourites window does (`resources/lib/favourites.py`, tests/test_favourites.py).
  `aeon.fav.stamp` changes whenever the favourites change (checked every 3 s on Home); the skin puts it in the
  row's path, as Kodi reloads a plugin list only when its path changes.

## 0.3.51 (skin 0.31.0)
- Fused Glass real frost: while Fused Glass shows a library window, the service follows the backdrop on screen
  (`$VAR[FG_BlurSrc]`) and makes a small blurred copy of it with Pillow (640 x 360, Gaussian blur; `blurcache.py`,
  `resources/lib/blur.py`) in `addon_data/script.aeon.helper/blur` (the newest 300 are kept). It publishes
  `Window(Home).Property(aeon.blur)` and `aeon.blur.src`; the skin lays the copy under its frosted panels. Pictures are
  read from Kodi's texture cache when they are there, else from their source. Tests: `tests/test_blur.py`.
- Recent searches (`searchhist.py`, `resources/lib/searches.py`): queries done in the skin's Search window (1150) are
  kept, newest first, at most eight, in `searches.json` and published as `aeon.search.1..8` / `aeon.search.count`.
  `RunScript(script.aeon.helper,search,N)` opens the Search window and types search N into its keyboard (JSON-RPC
  Input.SendText); `search,clear` forgets them. Tests: `tests/test_searches.py`.
- Planner week (`nextaired.publish_week`, `planner.week_counts`): for Home > Planner, today and the six days after it
  with how many episodes and films come out each day (`aeon.plw.N.day / .date / .count`).

## 0.3.50 (skin 0.29.0)
- Fused Glass theme: the service sets `aeon.fglass` (and `aeon.vglass`, as Fused Glass is built on Glass) when Kodi's
  theme is Fused Glass, and makes sure its colours (`colors/Fused Glass.xml`) are chosen. `theme,<aeon|glass|fused>`
  picks a theme; `theme` alone steps Aeon > Glass > Fused Glass. The palette picker leaves the Fused Glass colours out.

## 0.3.49 (skin 0.28.2)
- Planner: never during playback. A due read waits until playback (playing or paused) has been over for three
  minutes and no key has been pressed for three minutes, then starts; the service looks every minute (it looked every
  half hour and waited for ten idle minutes). The end of playback is timed by the helper, because Kodi's idle time
  keeps counting during a film. A read (also Update now) does not start while something plays and stops, keeping the
  old list, as soon as something starts (`planner.quiet_enough`).

## 0.3.48 (skin 0.28.2)
- Chapter pictures are cropped by the service as soon as a video with chapters and Trickplay sprites starts
  (`chapterwin.ChapterPictures`, chapter starts from Player.Chapters); the chapters dialog only adds its bookmarks.
- Planner: the next episodes come from TMDb Helper's details of each show that can still air (status not Ended or
  Canceled: 468 of 2,142 on the box), asked one at a time with a short pause (`planner.airing_candidates`,
  `planner.next_episode`). TMDb Helper's "library: airing next" list asked TMDb about every show in up to 40 threads,
  ran into TMDb's rate limit and slowed the box to a crawl for many minutes.

## 0.3.47 (skin 0.28.1)
- Chapter pictures: `RunScript(script.aeon.helper,chapthumbs)` (the chapters dialog opens it) crops the cell of the
  Trickplay sprites next to the playing video (`<video>.trickplay/<width> - <cols>x<rows>[ - <ms>]/N.jpg`) for every
  chapter and bookmark into `special://temp/aeonchap/` and publishes `aeon.chap.prefix`. Pillow from Kodi, or the copy
  service.trickplay installs. New `resources/lib/chapthumbs.py` with tests.
- Ratings of the video playing as `aeon.r.player.imdb / tmdb / rt / trakt` (Kodi's `VideoPlayer.Rating(name)` always
  returns the default rating).

## 0.3.46 (skin 0.28.0)
- Translated into the skin's 22 languages. The notifications, dialogs, Planner refresh names and context menu labels
  come from `resources/language` (ids 32000-32026, `resources/lib/lang.py`); English when a string is missing.

## 0.3.45 (skin 0.27.1)
- Icon and fanart.
- TMDb Helper and KarmaMole Skin Helper declared as optional imports.

## 0.3.44 (skin 0.27.0)
- Works with the new skin id `skin.aeon.fuse` (Glass Aeon is now Aeon Fuse).

## 0.3.43 (skin 0.26.0)
- Choose icon for Home menu items.
- Down to the Home rows waits for them to load.
- A Planner read that fails waits longer each time before the next try: 6, 12, 24 and 48 hours, then 4 days.

## 0.3.42 (skin 0.25.0)
- Planner list kept and merged safely, with an update interval and Update now.
- Palette colours for the palette picker.
- Menu theme switch.

## 0.3.41 (skin 0.24.0)
- Setup wizard: starts with the skin's own colours each time it opens.

## 0.3.40 (skin 0.23.0)
- Home menu: 13 positions. The wizard switches presets on and off: where they are, or in the first free position.

## 0.3.39 (skin 0.22.0)
- Setup wizard publishes the current theme and palette before it opens, and Finish applies both together. On Linux
  it then restarts Kodi; on Windows it asks for a restart.
- Refresh information: the progress shows as a toast with the episode being refreshed, then "Information refreshed".
- Dolby Vision P7 FEL / MEL: read from the media manager's `<name>.cmm_mediainfo.xml` when the .nfo does not say.
- Studio / network logos: the first studio of a title is published, so titles with several studios get a logo.
- `?info=trim` logs what a hand-back freed.

## 0.3.38 (skin 0.21.0)
- Memory hand-back on CoreELEC / Linux (`malloc_trim`), as chosen in Skin settings: when free memory falls to the
  minimum, or after the keys have rested; once as a video starts and once when it stops.
- Context menu items at every place, with their own arguments.
- KarmaMole is told which list is on screen for the Colors backdrop (Home spotlight, widget screens).
- Artwork colours are worked out inside the service. KarmaMole is no longer started as a new script per item, and no
  colours are worked out under the screensaver.
- An episode gives the page the colour of its own thumbnail.
- Files copied over by hand: Kodi reads the new addon.xml at start-up (`UpdateLocalAddons`).
- The Planner's TMDb Helper list is rebuilt at most once a fortnight, only when Kodi is idle and nothing plays.
- Font sets: a 12-point caption face for the section fonts.

## 0.3.37
- Skin settings > Context menu: Refresh information, Update library, Clean library, Take screenshot.
- A palette chosen in View settings shows at once.

## 0.3.34
- Home spotlight with the Colors background tells KarmaMole which list is the spotlight.

## 0.3.33
- Dolby Vision profile 7 chip (P7 FEL / MEL) from the film's .nfo.
- Palette in View settings.

## 0.3.32
- Planner titles carry genre, certificate, studio, rating, cast and network. An episode without a plot shows its show's.

## 0.3.31
- Home spotlight of a movie set: the ratings of the focused film.

## 0.3.30
- The chosen palette comes back when the theme returns to Aeon.

## 0.3.29
- Changing the theme (Aeon / Glass) reloads the skin.

## 0.3.28
- Trimmed clearlogos for the Low list.

## 0.3.27
- Home menu settings: Move up / Move down keep the highlight; Enable / Disable keeps the item; Choose type.

## 0.3.25
- Planner spotlight on Home.

## 0.3.24
- The Planner window with Day and Week views.

## 0.3.23
- Trailers: the trailer file next to a film, show, season or episode comes first.

## 0.3.22
- Online lists matched against the library.

## 0.3.21
- Progress line on posters.

## 0.3.20
- Artist page: Top tracks and Similar artists from Deezer's public API, matched against the library.

## 0.3.19
- Artist page: Top tracks and Similar artists from the library.

## 0.3.18
- Information page: TMDb reviews.

## 0.3.17
- Cinema mode: trailers of films in cinemas before a library film.

## 0.3.16
- Kiosk mode.

## 0.3.15
- Stacked row on Home.

## 0.3.14
- Skin settings > More options.

## 0.3.13
- Palettes.

## 0.3.12
- Low list: poster / thumbnail, counts and watched state.

## 0.3.5 - 0.3.11
- Fonts per section: a family for Home, Library, Headings, Settings pages and Player (0.3.5), more families
  (0.3.6, 0.3.9, 0.3.10), a preview in the family list (0.3.7), headings follow their section (0.3.11).
- Uptime as `8d 15h 2m` (0.3.8).

## 0.3.4
- Album count on every artist row.

## 0.3.2
- Home, System item: Version, System, Hardware and Library panels.

## 0.3.1
- Box colours from the poster on screen.

## 0.3.0
- Skin settings `daylight.*` carried over to `aeon.*` once.

## 0.2.0 - 0.2.4
- Every rating of the focused item (`aeon.r.*`) and premiere / finale marks (0.2.0).
- Library view settings (0.2.1), theme songs (0.2.2), the KarmaMole colour wash (0.2.3), Home spotlight trailers (0.2.4).

## 0.1.1
- Home menu settings: move, show / hide, rename, restore the default order.

## 0.1.0
- Library counts as Home properties.
