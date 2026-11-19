# Aeon Fuse Helper (script.aeon.helper)

**Project page:** [jonnypuma.github.io/#/script.aeon.helper](https://jonnypuma.github.io/#/script.aeon.helper) · **All add-ons and apps by jonnypuma:** [jonnypuma.github.io](https://jonnypuma.github.io/)

The helper add-on of the [Aeon Fuse](../skin.aeon.fuse) skin. The skin requires it. It works out what a Kodi skin
cannot do in XML and hands the results to the skin, mostly as `Window(Home)` properties and skin strings. Under
another skin its service does nothing.

- Kodi 21 / 22 / 23 (Python 3, `xbmc.python` 3.0.1)
- Licence: GPL-2.0-or-later
- Optional: TMDb Helper (`plugin.video.themoviedb.helper`) for the Planner and the online lists, and the KarmaMole
  Skin Helper (`script.karmamole.helper`) for the artwork colours. Each feature only appears when its add-on is installed.

## What it does

### Service (`service.py`, runs while Kodi runs)

- **Library counts:** films, shows, episodes, artists, albums and songs, refreshed after every scan or clean
  (`aeon.count.*`). Also the album count of each artist row.
- **Ratings:** every rating of the focused item (IMDb, TMDb, Rotten Tomatoes, Trakt) as `aeon.r.*`, because Kodi
  lists only carry the default rating; those of the video playing as `aeon.r.player.*` for the information screen.
- **Episode marks:** series and season premieres and finales.
- **Studio logos:** the first studio of a title, because Kodi joins all studios into one name that no logo file has.
- **Artwork colours:** worked out with the KarmaMole helper, for the Colors backdrop and the coloured boxes.
- **Clearlogos:** trimmed copies without their transparent border, kept in the add-on's data folder.
- **Theme songs, trailers and cinema mode:** trailer files next to the video come first.
- **Planner data:** upcoming episodes and films, read from TMDb Helper at most once a fortnight: the next episode of
  each show that can still air, one show at a time. Never during playback: a due read waits for three minutes after
  playback and three minutes without a key press, and stops when something starts playing.
- **Caches:** library titles and artist genres, kept for the online lists and the Similar artists row.
- **Memory hand-back on Linux / CoreELEC:** gives the memory Kodi has freed back to the system (`malloc_trim`), as
  chosen in Skin settings.
- **System panels:** uptime as `8d 15h 2m`.
- **Setting migration:** carries the old `daylight.*` skin settings over to `aeon.*` once.

### Script (`RunScript(script.aeon.helper,<command>)`, see `swap.py`)

| Command | What it does |
|---|---|
| `swap,<pos>,<-1\|1>`, `enable`, `toggle`, `type`, `icon,<pos>`, `reset` | Home menu: move, show / hide, choose the type or the icon of a position, restore the default order |
| `fonts` | Pick a font family for each section of the skin (`fontpick.py`) |
| `palette`, `theme`, `menutheme` | Palette, Aeon / Glass theme, Classic / Fuse menu theme |
| `options` | Skin settings > More options |
| `wizard,open` | Open the setup wizard (`wizard` alone runs the wizard's Finish step) |
| `planner,<command>` | Moves in the Planner window (`plannerwin.py`) |
| `chapthumbs` | Chapters dialog: pictures for each chapter and bookmark cropped from the Trickplay sprites next to the video (`chapterwin.py`) |
| `trailer,<command>` | Find and play the trailer of the focused item |
| `albumview` | From the music player controls to the playing album |
| `focusstrip,<n>`, `lyrics`, `ctx`, `rescan`, `tvgroup`, `review`, `android` | Smaller jobs of the skin's buttons |

### Lists (`plugin://script.aeon.helper/?info=...`, `plugin.py`)

- `online`: TMDb Helper lists matched against the library.
- `similar`, `toptracks`: the artist page rows (library and Deezer).
- `nextaired`: the Planner list.
- `playchannel`: play a live TV channel.
- `trim`: hand memory back now.

### Context menu (`context.py`)

Refresh information, Update library, Clean library and Take screenshot. Order and on / off are set in the skin under
Skin settings > Context menu.

## Files

- `resources/lib/`: the logic, mostly without Kodi imports so it can be tested outside Kodi.
- `resources/language/`: the helper's own texts (ids 32000 and up).
- `addon_data/script.aeon.helper/` (in Kodi's userdata): the caches and the trimmed logos.

## Languages

`resources/language/resource.language.<code>/strings.po` in English and the skin's 22 languages. Python code reads
them through `resources/lib/lang.py` (`L(32004)`), which falls back to the English text in that file.

## Tests

The modules in `resources/lib` that do not import Kodi have unit tests in `tests/`:

    python -m pytest tests

## Changes

See [CHANGELOG.md](CHANGELOG.md).
