# -*- coding: utf-8 -*-
"""Skin settings > System > Export / Import skin settings (skin 0.56.42): the file and what an import changes.
No Kodi imports here (tests/test_backup.py); settingsio.py does the dialogs and the JSON-RPC calls.

The file is JSON: {"format": "aeon-fuse-settings", "version": 1, "skin": "0.56.42", "saved": "2026-11-18 14:05",
"kodi": {"lookandfeel.skintheme": ..., "lookandfeel.skincolors": ..., "lookandfeel.font": ...},
"settings": {"<id>": true/false/"text", ...}} with every skin setting Kodi knows (Settings.GetSkinSettings)."""
import json

FORMAT = 'aeon-fuse-settings'
VERSION = 1
# Kodi's own settings that belong to the look: theme, colours (the palette) and Kodi's font setting
KODI = ('lookandfeel.skintheme', 'lookandfeel.skincolors', 'lookandfeel.font')
# set first: the service follows the theme with these switches, so they go in before Kodi's theme changes
FIRST = ('aeon.fglass', 'aeon.vglass')
# skin strings the helper writes while Kodi runs (a list's path ...): not settings, never saved or loaded
RUNTIME = 'aeon.rt.'


def build(skin_settings, kodi, skin_version, saved):
    """skin_settings: Settings.GetSkinSettings()['settings'] ([{'id', 'type', 'value'}]); kodi: {setting: value}"""
    values = {}
    for item in skin_settings or []:
        key = item.get('id')
        if not key or key.startswith(RUNTIME):
            continue
        value = item.get('value')
        values[key] = bool(value) if item.get('type') == 'boolean' else ('' if value is None else str(value))
    return {'format': FORMAT, 'version': VERSION, 'skin': skin_version, 'saved': saved,
            'kodi': dict((k, kodi[k]) for k in KODI if k in kodi), 'settings': values}


def dump(data):
    return json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False)


def load(text):
    """the file's data, or None when it is not an Export skin settings file"""
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        return None
    if not isinstance(data, dict) or data.get('format') != FORMAT or not isinstance(data.get('settings'), dict):
        return None
    if not isinstance(data.get('version'), int) or data['version'] > VERSION:
        return None
    return data


def plan(data, now):
    """what an import changes: [(id, value)] for the skin settings that differ from now ({id: value} like build()),
    the theme switches first. Settings the file does not have stay as they are (a file from an older version)."""
    out = []
    for key, value in data.get('settings', {}).items():
        if key.startswith(RUNTIME) or not isinstance(value, (bool, str)):
            continue
        if key in now and type(now[key]) is not type(value):
            continue                         # a switch in one version, a text in the other: leave it
        if now.get(key, False if isinstance(value, bool) else '') != value:
            out.append((key, value))
    out.sort(key=lambda kv: (kv[0] not in FIRST, kv[0]))
    return out


def kodi_plan(data, now):
    """Kodi's own settings that differ: [(setting, value)], the theme last (it reloads the skin)"""
    want = data.get('kodi') or {}
    out = [(k, want[k]) for k in KODI if k in want and want[k] != now.get(k)]
    out.sort(key=lambda kv: kv[0] == 'lookandfeel.skintheme')
    return out


def fonts_changed(changes):
    """the font choices are skin strings aeon.font*; Font.xml is written again when one of them changes"""
    return any(key.startswith('aeon.font') for key, _value in changes)


def builtin(key, value):
    """the Skin builtin for one change, when JSON-RPC refuses it (a setting Kodi does not know yet)"""
    if isinstance(value, bool):
        return ('Skin.SetBool(%s)' if value else 'Skin.Reset(%s)') % key
    if value == '':
        return 'Skin.Reset(%s)' % key
    return 'Skin.SetString(%s,"%s")' % (key, value.replace('\\', '\\\\').replace('"', '\\"'))


def file_name(saved):
    """aeon-fuse-settings-20261118-1405.json from '2026-11-18 14:05'"""
    return 'aeon-fuse-settings-%s.json' % saved.replace('-', '').replace(':', '').replace(' ', '-')
