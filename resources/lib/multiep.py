# -*- coding: utf-8 -*-
"""Episodes that share one video file, as one row (skin 0.56.23, helper 0.3.100; no Kodi imports).

Skin settings > Details > Episodes in one file as one row (Skin.HasSetting(aeon.ep.join), off by default): a season's
list comes from the helper (plugin ?info=episodes) with the episodes of one file joined (the approved canvas board
"1-2 LA X"; the user: "add each episode's duration to a total duration ... more than 2 episodes", then "if you use the
file duration from mediainfo then of course use that for total duration"):
- the numbers as a range, 1-2, 36-38 (or 1, 3 when they do not follow each other);
- the title once: part markers dropped ((1), Part 2 ...), the same title only once, different ones joined with " / ";
- the plot once when the parts say the same (or one holds the other), else each;
- the running time: the file's own (its video stream's duration) once, the parts' running times added up only when
  the file's is unknown. Kodi gives every part the whole file's length (The End 104 + 104, Looney Tunes Cartoons three
  times 12 min): adding those would double or triple it."""
import re

DASH = u'–'
PART = re.compile(r'(?:\s*[\(\[]\s*(?:part|pt\.?|teil|deel|del|partie|parte)?\s*(?:\d+|[ivx]+|one|two|three|four)\s*[\)\]]'
                  r'|[\s,:\-–]*\b(?:part|pt\.?|teil|deel|partie|parte)\s*(?:\d+|[ivx]+|one|two|three|four))\s*$', re.I)
SEASON_PATH = re.compile(r'^videodb://tvshows/titles/(\d+)/(-?\d+)/(?:\?.*)?$')


def season_path(path):
    """videodb://tvshows/titles/<show>/<season>/ (season -1: all seasons) -> (show, season), else None."""
    m = SEASON_PATH.match(path or '')
    return (int(m.group(1)), int(m.group(2))) if m else None


def order(episodes):
    return sorted(episodes, key=lambda e: (int(e.get('season') or 0), int(e.get('episode') or 0)))


def groups(episodes):
    """[[episode, ...], ...]: the episodes in season / episode order, those of one file together (first one's place)."""
    out, by_file = [], {}
    for e in order(episodes):
        f = e.get('file') or ''
        if f and f in by_file:
            by_file[f].append(e)
        else:
            g = [e]
            out.append(g)
            if f:
                by_file[f] = g
    return out


def shared(episodes):
    """True when at least two episodes have the same file."""
    files = [e.get('file') for e in episodes if e.get('file')]
    return len(files) != len(set(files))


def strip_part(title):
    t = (title or '').strip()
    s = PART.sub('', t).strip(' -,:')
    return s or t


def join_title(parts):
    seen, out = set(), []
    for e in parts:
        t = strip_part(e.get('title'))
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return ' / '.join(out)


def join_plot(parts):
    plots = []
    for e in parts:
        p = (e.get('plot') or '').strip()
        if not p or any(p in q for q in plots):
            continue
        plots = [q for q in plots if q not in p] + [p]
    return '\n\n'.join(plots)


def numbers(parts):
    """'1' for one episode, '1-2' / '36-38' for numbers that follow each other, else '1, 3'."""
    n = sorted(int(e.get('episode') or 0) for e in parts)
    if len(n) == 1:
        return str(n[0])
    if n == list(range(n[0], n[0] + len(n))):
        return '%d%s%d' % (n[0], DASH, n[-1])
    return ', '.join(str(x) for x in n)


def label(parts, title):
    """The row's label as Kodi writes it in a season, "01. LA X (1)"; a joined row "01-02. LA X" (or "01, 03. ...")."""
    n = sorted(int(e.get('episode') or 0) for e in parts)
    if len(n) > 1 and n == list(range(n[0], n[0] + len(n))):
        num = '%02d%s%02d' % (n[0], DASH, n[-1])
    else:
        num = ', '.join('%02d' % x for x in n)
    return '%s. %s' % (num, title)


def runtime(parts):
    """Seconds: the file's own duration (video stream), else the parts' running times added up."""
    for e in parts:
        for video in (e.get('streamdetails') or {}).get('video') or ():
            if int(video.get('duration') or 0) > 0:
                return int(video['duration'])
    return sum(int(e.get('runtime') or 0) for e in parts)


def code(parts, style=''):
    """The episode code of a joined row in the user's form (Skin.String(aeon.epcode)): '' 6x01-02, sxe S06E01-E02,
    sp S6 E1-2, bar S6 | E1-2, dot S6 * E1-2."""
    season = int(parts[0].get('season') or 0)
    n = sorted(int(e.get('episode') or 0) for e in parts)
    run = n == list(range(n[0], n[0] + len(n)))
    if style == 'sxe':
        tail = ('%sE%02d' % (DASH, n[-1])) if run else ''.join(', E%02d' % x for x in n[1:])
        return 'S%02dE%02d%s' % (season, n[0], tail)
    if style in ('sp', 'bar', 'dot'):
        sep = {'sp': ' ', 'bar': ' | ', 'dot': u' • '}[style]
        tail = ('%s%d' % (DASH, n[-1])) if run else ''.join(', %d' % x for x in n[1:])
        return 'S%d%sE%d%s' % (season, sep, n[0], tail)
    tail = ('%s%02d' % (DASH, n[-1])) if run else ''.join(', %02d' % x for x in n[1:])
    return '%dx%02d%s' % (season, n[0], tail)
