# -*- coding: utf-8 -*-
"""0.3.109 (skin 0.56.43) the Home spotlight's set strip (list 9441: the films of a set shown in a custom spotlight).

Its path used to be the skin variable Aeon_SetMembers, which reads the spotlight lists (Container(9411...).ListItem.DBType /
DBID). Kodi 22 froze on 2026-11-18 (box, entering Pictures): a list's loader thread (CDirectoryProvider::OnJobComplete ->
StartDirectoryJob) works the path out again under the list's own lock when it changed while loading, and reading another
list's item needs the GUI lock, which the screen thread held while it waited for that list's lock. The spotlight rotates,
so the path changed often. Now this works the same choice out over JSON-RPC (Kodi's main thread, as guiread does) and
writes it to Skin.String(aeon.rt.setrow) only when another set comes up; reading a skin string takes no GUI lock."""
import json

import xbmc

import guiread

# (n of $EXP[Aeon_H_Spot<n>], the spotlight list it shows)
SPOTS = ((1, 9411), (2, 9412), (3, 9413), (4, 9415), (5, 9416), (6, 9417), (7, 9418), (8, 9419), (9, 9420), (10, 9424))
KEY = 'aeon.rt.setrow'


def _rpc(method, params):
    try:
        return json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}))).get('result') or {}
    except Exception:
        return {}


class SetRow(object):
    EVERY = 1.0

    def __init__(self):
        self.last = None
        self.next = 0.0

    def tick(self, now):
        if now < self.next:
            return
        self.next = now + self.EVERY
        if xbmc.getSkinDir() != 'skin.aeon.fuse' or not guiread._plain_cond('Window.IsActive(home)'):
            return
        guiread._load_skin()
        conds = [guiread.expand('$EXP[Aeon_H_Spot%d] + String.IsEqual(Container(%d).ListItem.DBType,set)' % (n, c)) for n, c in SPOTS]
        got = _rpc('XBMC.GetInfoBooleans', {'booleans': conds})
        for (n, c), cond in zip(SPOTS, conds):
            if got.get(cond):
                name = 'Container(%d).ListItem.DBID' % c
                dbid = (_rpc('XBMC.GetInfoLabels', {'labels': [name]}).get(name) or '').strip()
                if dbid.isdigit():
                    path = 'videodb://movies/sets/%s/' % dbid
                    if path != self.last and path != xbmc.getInfoLabel('Skin.String(%s)' % KEY):
                        xbmc.executebuiltin('Skin.SetString(%s,%s)' % (KEY, path))
                    self.last = path
                return
