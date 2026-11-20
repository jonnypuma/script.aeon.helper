# -*- coding: utf-8 -*-
"""0.3.96: the service reads list labels on Kodi's main thread.

The box froze on 2026-11-16 (Kodi 22 RC2) after a film's information window closed: the Videos window cleared its
6,118 films (CFileItemList::Assign -> Clear, the list's lock held) and freeing their pictures waited for the GUI lock,
while this service's xbmc.getInfoLabel('ListItem...') held the GUI lock and waited for the list's lock. Neither let go.
Python's getInfoLabel / getCondVisibility run on the add-on's own thread; JSON-RPC XBMC.GetInfoLabels /
GetInfoBooleans hand the work to Kodi's main thread (CApplicationMessenger), which is the thread that changes the lists,
so the two locks can no longer be taken in the opposite order.

install() routes every label and condition that reads a list item (ListItem.*, Container(n).ListItem...) or walks a
whole list (Container.TotalWatched ...) through JSON-RPC; the rest (Container.Content / NumItems / IsUpdating, Window
properties, Skin settings, Player, System) stays a plain call. A skin variable ($VAR[...]) is worked out here
from the skin's own definitions with JSON-RPC conditions and labels while a media window is up. Each service tick
fetches the labels and conditions the last tick read in one call each (tick()) and those values serve the whole tick,
so a tick costs two round trips, not one per read (one round trip waits for Kodi's next frame)."""
import html
import json
import os
import re
import threading
import time

import xbmc
import xbmcvfs

FRESH = 0.25                  # a value fetched outside the current tick serves this long
# what reaches a media window's list under its lock: the focused item (ListItem.*, Container(n).ListItem...) and the
# counts that walk the whole list; Container.Content / FolderPath / NumItems / IsUpdating read no item and stay plain
RISKY = re.compile(r'listitem|container(\(\d+\))?\.(total|numall|numnonfolder|hasfiles|hasfolders|numselected)', re.I)
TOKEN = re.compile(r'\$(INFO|VAR|ESCINFO|ESCVAR|LOCALIZE|ADDON|NUMBER)\[', re.I)
_plain_label = xbmc.getInfoLabel
_plain_cond = xbmc.getCondVisibility
_lock = threading.Lock()
_labels = {}                  # name -> (time, value)
_bools = {}
_used_labels = set()          # read since the last tick(): fetched together at the next one
_used_bools = set()
_gen = [0]                    # tick number: what a tick fetched serves the whole tick
_skin = {'dir': None, 'vars': {}, 'exps': {}}


def _rpc(method, key, names):
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': {key: list(names)}})
    try:
        return json.loads(xbmc.executeJSONRPC(request)).get('result') or {}
    except Exception:
        return {}


def _store(table, got, names, now):
    with _lock:
        for name in names:
            table[name] = (now, _gen[0], got.get(name, False if table is _bools else ''))


def _fresh(hit):
    return hit is not None and (hit[1] == _gen[0] or time.time() - hit[0] < FRESH)


def tick():
    """start of a service tick: one JSON-RPC call for the labels and one for the conditions the last tick read"""
    with _lock:
        labels, bools = sorted(_used_labels), sorted(_used_bools)
        _used_labels.clear()
        _used_bools.clear()
        _gen[0] += 1
        if _gen[0] % 200 == 0:                   # forget what nobody read for a minute
            for table in (_labels, _bools):
                for name in [n for n, hit in table.items() if time.time() - hit[0] > 60]:
                    del table[name]
    now = time.time()
    if labels:
        _store(_labels, _rpc('XBMC.GetInfoLabels', 'labels', labels), labels, now)
    if bools:
        _store(_bools, _rpc('XBMC.GetInfoBooleans', 'booleans', bools), bools, now)


def _cached(table, used, name, method, key):
    with _lock:
        used.add(name)
        hit = table.get(name)
    if _fresh(hit):
        return hit[2]
    now = time.time()
    got = _rpc(method, key, [name])
    _store(table, got, [name], now)
    return table[name][2]


def label(name):
    if TOKEN.search(name):
        return var_text(name)
    if not RISKY.search(name):
        return _plain_label(name)
    return _cached(_labels, _used_labels, name, 'XBMC.GetInfoLabels', 'labels')


def cond(expression):
    if not RISKY.search(expression):
        return _plain_cond(expression)
    return bool(_cached(_bools, _used_bools, expression, 'XBMC.GetInfoBooleans', 'booleans'))


def install():
    """the service's own interpreter only: its modules call xbmc.getInfoLabel / getCondVisibility by attribute"""
    xbmc.getInfoLabel = label
    xbmc.getCondVisibility = cond


# ------------------------------------------------------------------ skin variables, worked out over JSON-RPC
def _load_skin():
    skin = xbmc.getSkinDir()
    if _skin['dir'] == skin:
        return
    variables, expressions = {}, {}
    folder = xbmcvfs.translatePath('special://skin/1080i/')
    try:
        names = [n for n in os.listdir(folder) if n.lower().endswith('.xml')]
    except OSError:
        names = []
    for name in names:
        try:
            with open(os.path.join(folder, name), encoding='utf-8') as handle:
                text = handle.read()
        except (OSError, UnicodeDecodeError):
            continue
        for match in re.finditer(r'<variable\s+name="([^"]+)"[^>]*>(.*?)</variable>', text, re.S):
            values = []
            for value in re.finditer(r'<value(?:\s+condition="([^"]*)")?\s*(?:/>|>(.*?)</value>)', match.group(2), re.S):
                values.append((html.unescape(value.group(1)) if value.group(1) is not None else None,
                               html.unescape(value.group(2) or '')))
            variables[match.group(1)] = values
        for match in re.finditer(r'<expression\s+name="([^"]+)"[^>]*>(.*?)</expression>', text, re.S):
            expressions[match.group(1)] = html.unescape(match.group(2).strip())
    _skin.update(dir=skin, vars=variables, exps=expressions)


def expand(condition, depth=0):
    """$EXP[name] -> [its expression], nested ones too"""
    if depth > 8 or '$EXP[' not in condition:
        return condition
    return expand(re.sub(r'\$EXP\[([^\]]+)\]', lambda m: '[%s]' % _skin['exps'].get(m.group(1), 'false'), condition),
                  depth + 1)


def tokens(text):
    """split a label into plain text and $WORD[...] parts (brackets inside a part, [COLOR] tags say, nest)"""
    out, at = [], 0
    for match in TOKEN.finditer(text):
        if match.start() < at:
            continue
        depth, end = 1, match.end()
        while end < len(text) and depth:
            depth += {'[': 1, ']': -1}.get(text[end], 0)
            end += 1
        if depth:
            break
        if match.start() > at:
            out.append(('text', text[at:match.start()]))
        out.append((match.group(1).upper(), text[match.end():end - 1]))
        at = end
    if at < len(text):
        out.append(('text', text[at:]))
    return out


def split_args(body):
    """$INFO[label,prefix,suffix]: commas outside brackets and parentheses"""
    parts, depth, start = [], 0, 0
    for i, char in enumerate(body):
        if char in '[(':
            depth += 1
        elif char in '])':
            depth -= 1
        elif char == ',' and depth == 0:
            parts.append(body[start:i])
            start = i + 1
    parts.append(body[start:])
    return parts


def render(text, depth=0):
    out = []
    for kind, body in tokens(text):
        if kind == 'text':
            out.append(body)
        elif kind in ('INFO', 'ESCINFO'):
            args = split_args(body)
            value = label(args[0].strip())
            if value:
                out.append((args[1] if len(args) > 1 else '') + value + (args[2] if len(args) > 2 else ''))
        elif kind in ('VAR', 'ESCVAR'):
            out.append(variable(split_args(body)[0].strip(), depth + 1))
        else:
            out.append(_plain_label('$%s[%s]' % (kind, body)))
    return ''.join(out).replace('$COMMA', ',')


def variable(name, depth=0):
    values = _skin['vars'].get(name)
    if values is None or depth > 8:
        return ''
    wanted = [expand(c) for c, _ in values if c]
    with _lock:
        missing = [c for c in wanted if not _fresh(_bools.get(c))]
        _used_bools.update(wanted)
    if missing:
        _store(_bools, _rpc('XBMC.GetInfoBooleans', 'booleans', missing), missing, time.time())
    for condition, text in values:
        if condition is None or _bools.get(expand(condition), (0, 0, False))[2]:
            return render(text, depth)
    return ''


def var_text(text):
    """a label with $VAR / $INFO parts: worked out here while a media window (Videos, Music ...) is up, where the
    lists are big and change under the reader; elsewhere Kodi does it as before"""
    if not _plain_cond('Window.IsMedia'):
        return _plain_label(text)
    _load_skin()
    if any(kind in ('VAR', 'ESCVAR') and split_args(body)[0].strip() not in _skin['vars'] for kind, body in tokens(text)):
        return _plain_label(text)
    return render(text)
