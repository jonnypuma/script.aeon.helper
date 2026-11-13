# Aeon Fuse Helper changelog

The helper is released together with the skin. Each version below names the skin version it came with. The skin's
`CHANGELOG.md` tells the whole story of each feature. Versions not listed here have no note of their own there.

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
