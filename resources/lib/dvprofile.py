# -*- coding: utf-8 -*-
"""Dolby Vision profile chip (P5, P7 FEL, P7 MEL, P8.1, P8.4 ...) from a film's .nfo (<hdrdetail>7FEL</hdrdetail>,
<hdrdetail>8.1</hdrdetail>, <hdrdetail>5</hdrdetail>) or, when the .nfo does not say (a media manager may write it
again without the tag), from the manager's <name>.cmm_mediainfo.xml (<dovi_profile>, <dovi_el_type>,
<dovi_bl_compat>). Kodi does not read either, so the helper looks it up for the item in focus. No Kodi imports."""
import re

_NFO = re.compile(r'^(\d{1,2})(?:\.(\d))?\s*(FEL|MEL)?$', re.I)


def _name(profile, sub=None, layer=None):
    """'P7 FEL', 'P8.1', 'P5'; '' for what is not a Dolby Vision profile number."""
    try:
        number = int(profile)
    except (TypeError, ValueError):
        return ''
    if number < 4 or number > 20:
        return ''
    text = 'P%d' % number
    if sub not in (None, '', '0') and number in (8, 9, 10):
        text += '.%s' % sub
    if layer and number == 7:
        text += ' ' + layer.upper()
    return text


def label(nfo_text):
    """'P7 FEL' / 'P8.1' / 'P5' ... / '' from the text of an .nfo."""
    for found in re.findall(r'<hdrdetail>\s*([^<]+?)\s*</hdrdetail>', nfo_text or '', re.I):
        match = _NFO.match(found.strip())
        if match:
            value = _name(match.group(1), match.group(2), match.group(3))
            if value:
                return value
    return ''


def label_cmm(xml_text):
    """The same from a media manager's <name>.cmm_mediainfo.xml: <dovi_profile>7</dovi_profile>
    <dovi_el_type>FEL</dovi_el_type>, <dovi_profile>8.1</dovi_profile> or <dovi_profile>8</dovi_profile> with
    <dovi_bl_compat>1</dovi_bl_compat>, <dovi_profile>5</dovi_profile>."""
    text = xml_text or ''
    profile = re.search(r'<dovi_profile>\s*(\d{1,2})(?:\.(\d))?\s*</dovi_profile>', text, re.I)
    if not profile:
        return ''
    layer = re.search(r'<dovi_el_type>\s*([A-Za-z]+)\s*</dovi_el_type>', text, re.I)
    compat = re.search(r'<dovi_bl_compat>\s*(\d)\s*</dovi_bl_compat>', text, re.I)
    sub = profile.group(2) or (compat.group(1) if compat else None)
    return _name(profile.group(1), sub, layer.group(1) if layer else None)


def side_paths(path):
    """Files that can tell the profile, in order: the .nfo files (nfo_paths), then <name>.cmm_mediainfo.xml.
    Returns (kind, path) pairs; kind 'nfo' or 'cmm'."""
    nfos = nfo_paths(path)
    if not nfos:
        return []
    return [('nfo', nfo) for nfo in nfos] + [('cmm', nfos[0][:-len('.nfo')] + '.cmm_mediainfo.xml')]


def nfo_paths(path):
    """Where the .nfo of a video file can be: <name>.nfo next to it, then movie.nfo in its folder."""
    if not path or '://' in path and path.split('://', 1)[0] in ('plugin', 'videodb', 'pvr'):
        return []
    sep = '\\' if '\\' in path and '/' not in path else '/'
    folder, _sep, name = path.rpartition(sep)
    if not folder:
        return []
    stem = name.rsplit('.', 1)[0] if '.' in name else name
    return [folder + sep + stem + '.nfo', folder + sep + 'movie.nfo']
