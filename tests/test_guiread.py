# -*- coding: utf-8 -*-
"""guiread against stand-in xbmc / xbmcvfs modules: which reads go over JSON-RPC, the per-tick batch, and skin
variables worked out from their definitions."""
import json
import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


class World(object):
    def __init__(self):
        self.labels = {}
        self.bools = {}
        self.plain = []          # names read with the plain calls
        self.calls = []          # (method, names) sent over JSON-RPC
        self.media = True


def install(world, skin_dir):
    xbmc = types.ModuleType('xbmc')
    xbmc.getSkinDir = lambda: 'skin.test'

    def plain_label(name):
        world.plain.append(name)
        return world.labels.get(name, '')

    def plain_cond(text):
        world.plain.append(text)
        if text == 'Window.IsMedia':
            return world.media
        return world.bools.get(text, False)

    def rpc(request):
        request = json.loads(request)
        key = 'labels' if request['method'] == 'XBMC.GetInfoLabels' else 'booleans'
        names = request['params'][key]
        world.calls.append((request['method'], tuple(names)))
        table = world.labels if key == 'labels' else world.bools
        return json.dumps({'result': dict((n, table.get(n, '' if key == 'labels' else False)) for n in names)})
    xbmc.getInfoLabel = plain_label
    xbmc.getCondVisibility = plain_cond
    xbmc.executeJSONRPC = rpc
    xbmcvfs = types.ModuleType('xbmcvfs')
    xbmcvfs.translatePath = lambda path: skin_dir
    sys.modules['xbmc'] = xbmc
    sys.modules['xbmcvfs'] = xbmcvfs
    sys.modules.pop('guiread', None)
    import guiread
    return guiread


SKIN = '''<includes>
<expression name="Busy">String.IsEqual(Window(Home).Property(x),1)</expression>
<expression name="Outer">$EXP[Busy] + Window.IsActive(videos)</expression>
<variable name="Fan">
    <value condition="$EXP[Outer] + !String.IsEmpty(ListItem.Art(fanart1))">$INFO[ListItem.Art(fanart1)]</value>
    <value condition="String.IsEqual(ListItem.DBType,episode)">$VAR[Show]</value>
    <value>$INFO[ListItem.Art(fanart),[COLOR red],[/COLOR]]</value>
</variable>
<variable name="Show"><value>$INFO[ListItem.Art(tvshow.fanart)]</value></variable>
</includes>'''


class GuiReadTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        with open(os.path.join(self.folder, 'Includes.xml'), 'w', encoding='utf-8') as handle:
            handle.write(SKIN)
        self.world = World()
        self.gr = install(self.world, self.folder)

    def test_plain_reads_stay_plain(self):
        self.world.labels['Window(Home).Property(a)'] = 'x'
        self.assertEqual(self.gr.label('Window(Home).Property(a)'), 'x')
        self.assertFalse(self.gr.cond('Player.HasVideo'))
        self.assertFalse(self.gr.cond('Container.Content(movies) + Integer.IsGreater(Container(9000).NumItems,0)'))
        self.assertEqual(self.gr.label('Container.FolderPath'), '')
        self.assertEqual(self.world.calls, [])
        self.gr.label('Container.TotalWatched')         # walks the list: main thread
        self.assertEqual(len(self.world.calls), 1)

    def test_list_reads_go_over_jsonrpc_and_batch_next_tick(self):
        self.world.labels.update({'ListItem.DBID': '7', 'Container(50).ListItem.Label': 'A'})
        self.world.bools['!String.IsEmpty(ListItem.Title)'] = True
        self.assertEqual(self.gr.label('ListItem.DBID'), '7')
        self.assertEqual(self.gr.label('Container(50).ListItem.Label'), 'A')
        self.assertTrue(self.gr.cond('!String.IsEmpty(ListItem.Title)'))
        self.assertEqual(len(self.world.calls), 3)
        self.assertNotIn('ListItem.DBID', self.world.plain)
        self.world.calls[:] = []
        self.gr.tick()                       # one call for the labels, one for the conditions
        self.assertEqual(sorted(m for m, _ in self.world.calls), ['XBMC.GetInfoBooleans', 'XBMC.GetInfoLabels'])
        self.world.calls[:] = []
        self.assertEqual(self.gr.label('ListItem.DBID'), '7')
        self.assertEqual(self.world.calls, [])  # served from the batch

    def test_tokens_nest_brackets(self):
        parts = self.gr.tokens('a $INFO[ListItem.Year,[COLOR red],[/COLOR]] b $VAR[X]')
        self.assertEqual(parts, [('text', 'a '), ('INFO', 'ListItem.Year,[COLOR red],[/COLOR]'), ('text', ' b '),
                                 ('VAR', 'X')])
        self.assertEqual(self.gr.split_args('ListItem.Art(fanart),[COLOR red],[/COLOR]'),
                         ['ListItem.Art(fanart)', '[COLOR red]', '[/COLOR]'])

    def test_variable_first_true_value(self):
        self.world.labels.update({'ListItem.Art(fanart1)': 'f1.jpg', 'ListItem.Art(fanart)': 'f.jpg',
                                  'ListItem.Art(tvshow.fanart)': 'show.jpg'})
        outer = '[[String.IsEqual(Window(Home).Property(x),1)] + Window.IsActive(videos)] + !String.IsEmpty(ListItem.Art(fanart1))'
        self.world.bools[outer] = True
        self.assertEqual(self.gr.label('$VAR[Fan]'), 'f1.jpg')
        self.world.bools[outer] = False
        self.gr._bools.clear()
        self.world.bools['String.IsEqual(ListItem.DBType,episode)'] = True
        self.assertEqual(self.gr.label('$VAR[Fan]'), 'show.jpg')
        self.gr._bools.clear()
        self.world.bools['String.IsEqual(ListItem.DBType,episode)'] = False
        self.assertEqual(self.gr.label('$VAR[Fan]'), '[COLOR red]f.jpg[/COLOR]')
        self.assertNotIn('$VAR[Fan]', self.world.plain)

    def test_variable_outside_media_windows_is_plain(self):
        self.world.media = False
        self.world.labels['$VAR[Fan]'] = 'kodi'
        self.assertEqual(self.gr.label('$VAR[Fan]'), 'kodi')

    def test_unknown_variable_is_plain(self):
        self.world.labels['$VAR[Nope]'] = 'kodi'
        self.assertEqual(self.gr.label('$VAR[Nope]'), 'kodi')


if __name__ == '__main__':
    unittest.main()
