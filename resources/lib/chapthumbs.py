"""Chapter and bookmark thumbnails from Trickplay sprites. No Kodi imports.

service.trickplay (and Jellyfin) keep seek-bar previews next to the video as sprite sheets:
    <video name>.trickplay/<width> - <cols>x<rows>[ - <interval ms>]/0.jpg, 1.jpg, ...
Each sheet is a grid of cols x rows thumbnails, one every <interval> ms (10000 when the folder name has no interval),
left to right, top to bottom, sheet after sheet. The chapters dialog (VideoOSDBookmarks) lists each chapter and
bookmark with its start in seconds (ListItem.Property(resumepoint)); the thumbnail for that moment is one cell.
"""
import re

DEFAULT_INTERVAL_MS = 10000
PREFERRED_WIDTH = 320

_RES_RE = re.compile(r'^(?P<width>\d+) - (?P<cols>\d+)x(?P<rows>\d+)(?: - (?P<interval>\d+))?$')
_TILE_RE = re.compile(r'^(\d+)\.jpe?g$', re.IGNORECASE)
_KEY_RE = re.compile(r'[^0-9.]')


def parse_resolution(name):
    """'320 - 10x10 - 10000' -> (320, 10, 10, 10000); '320 - 10x10' -> (320, 10, 10, 10000); else None."""
    match = _RES_RE.match((name or '').strip())
    if not match:
        return None
    width, cols, rows = int(match.group('width')), int(match.group('cols')), int(match.group('rows'))
    interval = int(match.group('interval')) if match.group('interval') else DEFAULT_INTERVAL_MS
    if not (width and cols and rows and interval):
        return None
    return width, cols, rows, interval


def choose_resolution(names, preferred=PREFERRED_WIDTH):
    """The sidecar folder to use: the preferred width, else the smallest wider one, else the widest narrower one.
    Among folders of the same width the shortest interval wins (finer previews). Returns (name, parsed) or None."""
    parsed = [(name, parse_resolution(name)) for name in names or ()]
    parsed = [(name, res) for name, res in parsed if res]
    if not parsed:
        return None
    wider = [item for item in parsed if item[1][0] >= preferred]
    if wider:
        return min(wider, key=lambda item: (item[1][0], item[1][3]))
    return max(parsed, key=lambda item: (item[1][0], -item[1][3]))


def tile_order(names):
    """The sprite sheets in playback order: 0.jpg, 1.jpg, ..., 10.jpg (numeric, not alphabetical)."""
    tiles = []
    for name in names or ():
        match = _TILE_RE.match(name)
        if match:
            tiles.append((int(match.group(1)), name))
    return [name for _number, name in sorted(tiles)]


def cell(seconds, interval_ms, cols, rows, tile_count):
    """(sheet index, column, row) of the thumbnail shown at `seconds`. Past the last sheet: its last cell."""
    if tile_count <= 0 or cols <= 0 or rows <= 0 or interval_ms <= 0:
        return None
    index = int(max(float(seconds), 0.0) * 1000 // interval_ms)
    per_sheet = cols * rows
    sheet, position = divmod(index, per_sheet)
    if sheet >= tile_count:
        sheet, position = tile_count - 1, per_sheet - 1
    column, row = position % cols, position // cols
    return sheet, column, row


def sidecar_root(playing_file):
    """The .trickplay folder of a video: the path without its extension, plus '.trickplay'. None for streams."""
    path = playing_file or ''
    lower = path.lower()
    if not path or lower.startswith(('plugin://', 'http://', 'https://', 'pvr://', 'upnp://')):
        return None
    slash = max(path.rfind('/'), path.rfind('\\'))
    dot = path.rfind('.')
    base = path[:dot] if dot > slash else path
    return base + '.trickplay'


def file_key(resumepoint):
    """The part of the thumbnail's file name that comes from ListItem.Property(resumepoint) ('104.000000'): only
    digits and dots, so it is a safe file name and the skin can build the same name from the property."""
    return _KEY_RE.sub('', resumepoint or '')


def chapter_starts(chapters_label, count, total_seconds):
    """Player.Chapters ('0.00000,3.06517,3.06517,20.98463,...': start / end percentages of each chapter, the last
    chapter's end left out) -> the start in seconds of each of the `count` chapters."""
    starts = []
    for value in (chapters_label or '').split(','):
        try:
            pct = float(value)
        except ValueError:
            continue
        if not starts or abs(pct - starts[-1]) > 1e-6:
            starts.append(pct)
    if count:
        starts = starts[:count]
    return [pct * total_seconds / 100.0 for pct in starts]
