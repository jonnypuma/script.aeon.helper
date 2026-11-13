# -*- coding: utf-8 -*-
"""Recent searches for the skin (Home > Search shows them; 0.31.0).

The service watches the Search window (1150): once the keyboard has closed on a query, the query is added to
addon_data/script.aeon.helper/searches.json and published as Window(Home).Property(aeon.search.1..8) with
aeon.search.count. RunScript(script.aeon.helper,search,N) opens the Search window and types recent search N into
its keyboard (JSON-RPC Input.SendText, done), so the results load as if typed; search,clear forgets them all."""
import json
import os

import xbmc
import xbmcgui
import xbmcvfs

from resources.lib import searches

FILE = 'special://profile/addon_data/script.aeon.helper/searches.json'
WATCH = 'Window.IsActive(1150) + !Window.IsActive(virtualkeyboard)'


def path():
    p = xbmcvfs.translatePath(FILE)
    folder = os.path.dirname(p)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    return p


def load():
    try:
        with open(path(), 'r', encoding='utf-8') as handle:
            data = json.load(handle)
        return [q for q in data if isinstance(q, str)][:searches.LIMIT]
    except (OSError, ValueError):
        return []


def save(history):
    p = path()
    with open(p + '.tmp', 'w', encoding='utf-8') as handle:
        json.dump(history, handle, ensure_ascii=False)
    os.replace(p + '.tmp', p)


def publish(history):
    home = xbmcgui.Window(10000)
    for i in range(searches.LIMIT):
        home.setProperty('aeon.search.%d' % (i + 1), history[i] if i < len(history) else '')
    home.setProperty('aeon.search.count', str(len(history)))


def tick(state):
    """Called from the service loop: publish once at start, then record queries done in the Search window."""
    if 'search' not in state:
        state['search'] = ''
        publish(load())
    if not xbmc.getCondVisibility(WATCH):
        state['search'] = ''
        return
    query = searches.clean(xbmc.getInfoLabel('Control.GetLabel(9001).index(1)'))
    if not query or query == state['search']:
        return
    state['search'] = query
    history = searches.add(load(), query)
    save(history)
    publish(history)


def run(arg):
    """search,N (1-based): open the Search window with recent search N; search,clear: forget them all."""
    if arg == 'clear':
        save([])
        publish([])
        return
    history = load()
    try:
        query = history[int(arg) - 1]
    except (ValueError, IndexError):
        return
    xbmc.executebuiltin('ActivateWindow(1150)')
    # the window opens the keyboard by itself when its field is empty; type the query there and press Done
    for _ in range(40):
        xbmc.sleep(100)
        if xbmc.getCondVisibility('Window.IsActive(virtualkeyboard)'):
            break
    else:
        return
    xbmc.sleep(200)
    xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'Input.SendText',
                                    'params': {'text': query, 'done': True}}))
    # on top again, though the service will also see it
    history = searches.add(history, query)
    save(history)
    publish(history)
