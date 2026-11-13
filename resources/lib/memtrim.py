# -*- coding: utf-8 -*-
"""Hand memory that Kodi has freed back to the system (glibc malloc_trim). Kodi on Linux keeps freed small blocks in
its per-thread malloc arenas; on a 4 GB CoreELEC box those arenas grew to 1.5 GB of resident memory. No Kodi imports."""
import ctypes
import ctypes.util
import sys

_LIBC = None


def _libc():
    global _LIBC
    if _LIBC is None:
        _LIBC = False
        if sys.platform.startswith('linux'):
            try:
                name = ctypes.util.find_library('c') or 'libc.so.6'
                lib = ctypes.CDLL(name)
                lib.malloc_trim.argtypes = [ctypes.c_size_t]
                lib.malloc_trim.restype = ctypes.c_int
                _LIBC = lib
            except (OSError, AttributeError):
                _LIBC = False
    return _LIBC


def available():
    return bool(_libc())


def trim():
    """malloc_trim(0): 1 when memory was released, 0 when there was nothing to release, None where it does not exist."""
    lib = _libc()
    if not lib:
        return None
    return lib.malloc_trim(0)


def meminfo_mb(path='/proc/meminfo'):
    """(total, available) system memory in MB (Linux), else (None, None)."""
    found = {}
    try:
        with open(path) as handle:
            for line in handle:
                key, _, rest = line.partition(':')
                if key in ('MemTotal', 'MemAvailable'):
                    found[key] = int(rest.split()[0]) // 1024
    except (IOError, OSError, ValueError, IndexError):
        pass
    return found.get('MemTotal'), found.get('MemAvailable')


# Skin settings > Motion, memory, reset > Memory hand-back:
#   'free' (default): keep at least free_mb of the system's memory free (Skin.String(aeon.memtrim.free), default 1 GB).
#           Within EARLY_MB above that line the trim waits for a pause in key presses (not felt); below it, at once.
#   'idle': trim once the keys have rested for Skin.String(aeon.memtrim.idle) seconds (2-30, default 5), not during
#           a video.
# In both modes it is done at once when less than EMERGENCY_MB is free.
# Video: one trim as a video starts (what browsing left behind goes back before the buffers fill) and one when it
# stops. While it plays, only a real shortage counts: free memory under the minimum for VIDEO_HOLD_S (a seek or a
# filling buffer can dip for a moment). A trim holds the allocator for 40-260 ms; at worst one dropped frame.
FREE_DEFAULT_MB = 1024
IDLE_DEFAULT_S = 5
IDLE_RANGE = (2, 30)
EARLY_MB = 256
EMERGENCY_MB = 384
VIDEO_HOLD_S = 10
COOLDOWN_S = 20        # never two trims closer than this
STALE_S = 120          # after a trim that gave back almost nothing, wait this long (except in an emergency)
STALE_MB = 50


def settings(mode, idle_s, free_mb):
    """The three skin strings -> ('free' | 'idle', seconds, MB), with defaults and limits."""
    mode = 'idle' if (mode or '').strip().lower() == 'idle' else 'free'
    try:
        idle_s = min(max(int(idle_s), IDLE_RANGE[0]), IDLE_RANGE[1])
    except (TypeError, ValueError):
        idle_s = IDLE_DEFAULT_S
    try:
        free_mb = max(int(free_mb), EMERGENCY_MB)
    except (TypeError, ValueError):
        free_mb = FREE_DEFAULT_MB
    return mode, idle_s, free_mb


def decide(mode, available, now, last_at, last_freed, paused=False, rested=False, video=False,
           free_mb=FREE_DEFAULT_MB, low_since=None):
    """'now' when a trim should run, else None.
    available: free system memory in MB (None off Linux); last_at: time of the last trim (0 = never); last_freed: MB
    it gave back (None = never); paused: no key for 2 s; rested: the keys have rested for the idle time since they
    were last used; video: a video plays; low_since: since when free memory has been at or under free_mb."""
    if available is None:
        return None
    if now - last_at < COOLDOWN_S:
        return None
    if available < EMERGENCY_MB:
        return 'now'
    if last_freed is not None and last_freed < STALE_MB and now - last_at < STALE_S:
        return None
    if video:
        if available <= free_mb and low_since is not None and now - low_since >= VIDEO_HOLD_S:
            return 'now'
        return None
    if mode == 'idle':
        return 'now' if rested else None
    if available <= free_mb:
        return 'now'
    if available <= free_mb + EARLY_MB and paused:
        return 'now'
    return None


def video_edge(was_video, video, now, last_at):
    """'start' / 'stop' when a video has just started or stopped (a trim is due then), else None. Not within 5 s
    of another trim."""
    if bool(was_video) == bool(video) or now - last_at < 5:
        return None
    return 'start' if video else 'stop'


def rss_mb():
    """Resident memory of this process in MB (Linux), else None."""
    try:
        with open('/proc/self/status') as handle:
            for line in handle:
                if line.startswith('VmRSS:'):
                    return int(line.split()[1]) // 1024
    except (IOError, OSError, ValueError, IndexError):
        pass
    return None
