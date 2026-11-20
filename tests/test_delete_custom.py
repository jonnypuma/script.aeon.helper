import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from resources.lib import homemenu


def test_remove_moves_items_up():
    pos = ['movies', 'custom2', 'tv', 'custom5'] + ['off'] * 20
    hid = [False, True, False, True] + [False] * 20
    new, newhid = homemenu.remove(pos, hid, 2)
    assert new[:4] == ['movies', 'tv', 'custom5', 'off']
    assert newhid[:4] == [False, False, True, False]
    assert len(new) == 24 and len(newhid) == 24


def test_remove_last_and_out_of_range():
    pos = ['movies', 'custom1'] + ['off'] * 22
    new, _ = homemenu.remove(pos, [False] * 24, 2)
    assert homemenu.is_tail(new, 2)
    same, _ = homemenu.remove(pos, [False] * 24, 0)
    assert same == pos


def test_clear_custom_node(monkeypatch=None):
    import types
    sys.modules.setdefault('xbmcvfs', types.ModuleType('xbmcvfs'))
    import menufile
    menu = [{'guid': 'guid-aeon0013', 'label': 'Kids', 'icon': 'x.png', 'path': 'p', 'target': 'videos',
             'submenu': [{'label': 'a'}], 'widgets': [{'label': 'w'}]}]
    assert menufile.clear_custom_node(menu, 2)
    assert menu[0]['label'] == 'Custom item 2' and menu[0]['widgets'] == [] and menu[0]['submenu'] == []
    assert menu[0]['guid'] == 'guid-aeon0013'
    assert not menufile.clear_custom_node(menu, 2)
    assert not menufile.clear_custom_node(menu, 3)


def test_changed_only():
    pos = ['movies', 'custom2', 'tv', 'music'] + ['off'] * 20
    new, _ = homemenu.remove(pos, [False] * 24, 2)
    assert homemenu.changed(pos, new) == [2, 3, 4]
