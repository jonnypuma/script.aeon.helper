# -*- coding: utf-8 -*-
"""Mediainfo sidecars next to a video file (0.3.97): <name>.cmm_mediainfo.xml from Curator Media Manager (read first)
or <name>-mediainfo.xml from tinyMediaManager (MediaArea's MediaInfo XML). What Kodi's library does not know: the
source (UHD Remux, Blu-ray, WEB-DL, DVD ...), the edition, every audio and subtitle track, the chapters, the bitrate.

Pure functions (no Kodi): side_paths(path), parse(kind, text) -> info dict, props(info, language) -> the
Window(Home) properties aeon.mi.* the skin shows (strings, '' when unknown)."""
import re
import xml.etree.ElementTree as ET

CURATOR = 'Curator Media Manager'
TMM = 'tinyMediaManager'


# 0.3.114: one short name per container everywhere (a Curator sidecar said "Matroska", tinyMediaManager's was mapped)
CONTAINERS = {'matroska': 'MKV', 'mkv': 'MKV', 'webm': 'WEBM', 'mpeg-4': 'MP4', 'mp4': 'MP4', 'quicktime': 'MOV', 'avi': 'AVI',
              'bdav': 'M2TS', 'm2ts': 'M2TS', 'mpeg-ts': 'TS', 'ts': 'TS', 'mpeg-ps': 'MPG', 'dvd video': 'VOB'}


def container_name(text):
    t = (text or '').strip()
    return CONTAINERS.get(t.lower(), t.upper())


def side_paths(path):
    """[(kind, side file)] in the order they are read; [] for paths that have no folder of files"""
    if not path or '://' in path and path.split('://', 1)[0] in ('plugin', 'videodb', 'musicdb', 'pvr', 'stack', 'upnp'):
        return []
    sep = '\\' if '\\' in path and '/' not in path else '/'
    folder, _s, name = path.rpartition(sep)
    if not folder:
        return []
    stem = name.rsplit('.', 1)[0] if '.' in name else name
    return [('cmm', folder + sep + stem + '.cmm_mediainfo.xml'), ('tmm', folder + sep + stem + '-mediainfo.xml')]


# ------------------------------------------------------------------------------------------------- the source
_SOURCES = (                                      # (pattern over the dotted lower-case name, label); first match wins
    (r'remux', 'Remux'),
    (r'(?<![a-z])(blu-?ray|bdrip|brrip|bdremux|bd25|bd50|bd66|bd100)(?![a-z])', 'Blu-ray'),
    (r'(?<![a-z])(web-?dl|webdl)(?![a-z])', 'WEB-DL'),
    (r'(?<![a-z])web-?rip(?![a-z])', 'WEBRip'),
    (r'(?<![a-z])web(?![a-z])', 'WEB'),
    (r'(?<![a-z])hd-?dvd(?![a-z])', 'HD DVD'),
    (r'(?<![a-z])(dvd-?rip|dvd5|dvd9|dvdr|dvd)(?![a-z])', 'DVD'),
    (r'(?<![a-z])(hdtv|pdtv|dsr|tvrip)(?![a-z])', 'HDTV'),
    (r'(?<![a-z])(vhs|vhsrip)(?![a-z])', 'VHS'),
)


def guess_source(name, height=0):
    """the source from a release name ("Get.Hard.2015...2160p.MA.WEB-DL..." -> WEB-DL); UHD before Remux / Blu-ray at
    2160 lines (or when the name says uhd / 2160p)"""
    n = (name or '').lower().replace(' ', '.').replace('_', '.')
    uhd = (height or 0) >= 2000 or bool(re.search(r'(?<![a-z0-9])(2160p|uhd|4k)(?![a-z0-9])', n))
    for pat, label in _SOURCES:
        if re.search(pat, n):
            if label == 'Remux':
                return 'UHD Remux' if uhd else 'Blu-ray Remux' if re.search(r'blu-?ray|bd', n) or not re.search(r'dvd', n) else 'DVD Remux'
            if label == 'Blu-ray' and uhd:
                return 'UHD Blu-ray'
            return label
    return ''


_EDITIONS = (
    (r"director'?s?.?cut|(?<![a-z])dc(?![a-z])", "Director's Cut"), (r'extended', 'Extended'), (r'theatrical', 'Theatrical'),
    (r'unrated', 'Unrated'), (r'uncut', 'Uncut'), (r'imax', 'IMAX'), (r'final.?cut', 'Final Cut'), (r'ultimate', 'Ultimate'),
    (r'remastered', 'Remastered'), (r'criterion', 'Criterion'), (r'special.?edition', 'Special Edition'),
)


def guess_edition(name):
    n = (name or '').lower().replace(' ', '.').replace('_', '.')
    for pat, label in _EDITIONS:
        if re.search(pat, n):
            return label
    return ''


# ------------------------------------------------------------------------------------------------- reading
def _txt(el, tag, default=''):
    if el is None:
        return default
    x = el.find(tag)
    return (x.text or '').strip() if x is not None and x.text else default


def _num(s, kind=float):
    try:
        return kind(str(s).replace(',', '.').split()[0])
    except (TypeError, ValueError, IndexError):
        return None


def _strip_ns(text):
    return re.sub(r'\sxmlns(:\w+)?="[^"]*"', '', text, count=2)


def parse(kind, text):
    """the info dict of a sidecar (keys: from, name, source, format, vsource, edition, container, size, seconds, mbps, vcodec, vprofile,
    width, height, fps, bitdepth, hdr, hybrid, three_d, chapters, audio [{codec, channels, lang, title, default}],
    subs [{lang, title, sdh, forced, default}]); None when the text is not that kind of file"""
    if not text:
        return None
    try:
        root = ET.fromstring(_strip_ns(text.strip().lstrip('﻿')))
    except ET.ParseError:
        return None
    if kind == 'cmm' and root.tag == 'mediainfo':
        return _cmm(root)
    if kind == 'tmm' and root.tag == 'MediaInfo':
        return _tmm(root)
    return None


def _cmm(root):
    f = root.find('file')
    if f is None:
        return None
    name = _txt(f, 'name')
    height = _num(_txt(f, 'height'), int) or 0
    hdr = _txt(f, 'hdr_format').lower()
    info = {
        'from': CURATOR, 'name': name,
        'source': _txt(f, 'source_format') or _txt(f, 'video_source') or guess_source(name, height),
        # 0.3.102 the parts on their own for their chips: the disc / stream it came from, the release format
        'vsource': _txt(f, 'video_source'), 'format': _txt(f, 'source_format') or guess_source(name, height),
        'edition': _txt(f, 'edition') or guess_edition(name),
        'container': container_name(_txt(f, 'container')),
        'size': _num(_txt(f, 'size'), int), 'seconds': _num(_txt(f, 'duration_seconds')),
        'mbps': _num(_txt(f, 'bitrate_mbps')),
        'vcodec': _txt(f, 'video_codec'), 'vprofile': _txt(f, 'video_profile'),
        'width': _num(_txt(f, 'width'), int) or 0, 'height': height, 'resolution': _txt(f, 'resolution'),
        'fps': _num(_txt(f, 'fps')), 'bitdepth': _num(_txt(f, 'bit_depth'), int),
        'hdr': {'dovi': 'Dolby Vision', 'dolbyvision': 'Dolby Vision', 'dv': 'Dolby Vision', 'hdr10': 'HDR10',
                'hdr10+': 'HDR10+', 'hdr10plus': 'HDR10+', 'hlg': 'HLG', 'sdr': ''}.get(hdr, hdr.upper() if hdr else ''),
        'hybrid': _txt(f, 'is_hybrid').lower() == 'true', 'three_d': _txt(f, 'is_3d').lower() == 'true',
        'chapters': _num(_txt(f, 'chapters'), int) or 0,
        'audio': [], 'subs': [],
    }
    for t in root.findall('audio_tracks/track'):
        info['audio'].append({'codec': _txt(t, 'codec'), 'channels': _txt(t, 'channels'), 'lang': _txt(t, 'lang'),
                              'title': _txt(t, 'title'), 'default': _txt(t, 'default').lower() == 'true'})
    for t in root.findall('subtitle_tracks/track'):
        flags = _txt(t, 'flags').lower()
        title = _txt(t, 'title')
        info['subs'].append({'lang': _txt(t, 'lang'), 'title': title, 'sdh': 'sdh' in flags or 'sdh' in title.lower(),
                             'forced': 'forced' in flags or 'forced' in title.lower(), 'default': _txt(t, 'default').lower() == 'true'})
    for t in root.findall('external_subtitles/track') + root.findall('external_subtitles/subtitle'):
        info['subs'].append({'lang': _txt(t, 'lang'), 'title': _txt(t, 'title'), 'sdh': 'sdh' in _txt(t, 'flags').lower(),
                             'forced': False, 'default': False})
    return info


_AUDIO_NAMES = (('dts xll x', 'DTS:X'), ('dts xll', 'DTS-HD MA'), ('dts-hd master audio', 'DTS-HD MA'), ('dts xbr', 'DTS-HD HRA'),
                ('truehd atmos', 'TrueHD Atmos'), ('mlp fba 16-ch', 'TrueHD Atmos'), ('mlp fba', 'TrueHD'), ('truehd', 'TrueHD'),
                ('e-ac-3 joc', 'DD+ Atmos'), ('e-ac-3', 'DD+'), ('ac-3', 'DD'), ('dts', 'DTS'), ('aac', 'AAC'), ('flac', 'FLAC'),
                ('pcm', 'PCM'), ('opus', 'Opus'), ('mpeg audio', 'MP3'))


def _audio_name(fmt, commercial, additional):
    s = ('%s %s %s' % (fmt or '', additional or '', commercial or '')).lower()
    if 'atmos' in s and 'truehd' in s or 'mlp fba 16-ch' in s:
        return 'TrueHD Atmos'
    if 'atmos' in s and ('e-ac-3' in s or 'dolby digital plus' in s):
        return 'DD+ Atmos'
    if 'dts:x' in s or 'xll x' in s:
        return 'DTS:X'
    for key, name in _AUDIO_NAMES:
        if key in s:
            return name
    return (commercial or fmt or '').strip()


def _channels(n):
    n = _num(n, int)
    return {1: '1.0', 2: '2.0', 3: '2.1', 6: '5.1', 7: '6.1', 8: '7.1'}.get(n, str(n) if n else '')


def _tmm(root):
    tracks = root.findall('media/track')
    by = lambda kind: [t for t in tracks if t.get('type') == kind]  # noqa: E731
    g = (by('General') or [None])[0]
    v = (by('Video') or [None])[0]
    name = _txt(g, 'FileName') or _txt(g, 'FileNameExtension')
    height = _num(_txt(v, 'Height'), int) or 0
    hdr_s = ('%s %s' % (_txt(v, 'HDR_Format'), _txt(v, 'HDR_Format_Commercial'))).lower()
    hdr = ''
    if 'dolby vision' in hdr_s:
        hdr = 'Dolby Vision'
    elif 'hdr10+' in hdr_s or '2094' in hdr_s:
        hdr = 'HDR10+'
    elif 'hdr10' in hdr_s or '2086' in hdr_s or _txt(v, 'transfer_characteristics') == 'PQ':
        hdr = 'HDR10'
    elif 'hlg' in hdr_s or _txt(v, 'transfer_characteristics') == 'HLG':
        hdr = 'HLG'
    menu = (by('Menu') or [None])[0]
    chapters = 0
    if menu is not None:
        b, e = _num(_txt(menu, 'Chapters_Pos_Begin'), int), _num(_txt(menu, 'Chapters_Pos_End'), int)
        chapters = (e - b) if b is not None and e is not None and e > b else len([c for c in menu if c.tag.startswith('_')])
    bitrate = _num(_txt(g, 'OverallBitRate'))
    info = {
        'from': TMM, 'name': name,
        'source': guess_source(name, height), 'format': guess_source(name, height), 'vsource': '',
        'edition': guess_edition(name),
        'container': container_name(_txt(g, 'Format')),
        'size': _num(_txt(g, 'FileSize'), int), 'seconds': _num(_txt(g, 'Duration')),
        'mbps': round(bitrate / 1e6, 2) if bitrate else None,
        'vcodec': _txt(v, 'Format'), 'vprofile': (_txt(v, 'Format_Profile').split('@')[0]),
        'width': _num(_txt(v, 'Width'), int) or 0, 'height': height, 'resolution': '',
        'fps': _num(_txt(v, 'FrameRate')), 'bitdepth': _num(_txt(v, 'BitDepth'), int),
        'hdr': hdr, 'hybrid': 'dolby vision' in hdr_s and ('2086' in hdr_s or 'hdr10' in hdr_s),
        'three_d': bool(_txt(v, 'MultiView_Count')), 'chapters': chapters, 'audio': [], 'subs': [],
    }
    for t in by('Audio'):
        info['audio'].append({'codec': _audio_name(_txt(t, 'Format'), _txt(t, 'Format_Commercial_IfAny') or _txt(t, 'Format_Commercial'), _txt(t, 'Format_AdditionalFeatures')),
                              'channels': _channels(_txt(t, 'Channels')), 'lang': _txt(t, 'Language_String3') or _txt(t, 'Language'),
                              'title': _txt(t, 'Title'), 'default': _txt(t, 'Default').lower() == 'yes'})
    for t in by('Text'):
        title = _txt(t, 'Title')
        info['subs'].append({'lang': _txt(t, 'Language_String3') or _txt(t, 'Language'), 'title': title,
                             'sdh': 'sdh' in title.lower() or 'hearing' in title.lower(), 'forced': _txt(t, 'Forced').lower() == 'yes',
                             'default': _txt(t, 'Default').lower() == 'yes'})
    return info


# ------------------------------------------------------------------------------------------------- what the skin shows
DOT = ' · '


def _res(info):
    h, w = info.get('height') or 0, info.get('width') or 0
    if info.get('resolution'):
        return info['resolution'].replace('2160p', '4K')
    if h >= 1600 or w >= 3200:
        return '4K'
    if h >= 1000 or w >= 1800:
        return '1080p'
    if h >= 700 or w >= 1200:
        return '720p'
    return '%dp' % h if h else ''


def _size(n):
    if not n:
        return ''
    gb = n / 1e9
    return '%.1f GB' % gb if gb >= 1 else '%d MB' % round(n / 1e6)


def _audio_line(a, language):
    parts = [x for x in (a['codec'], a['channels']) if x]
    s = ' '.join(parts)
    lang = language(a['lang']) if a.get('lang') else ''
    if lang:
        s = '%s (%s)' % (s, lang) if s else lang
    title = a.get('title') or ''
    # the title when it says more than codec + channels (a commentary, an isolated score, the original mix)
    if title and title.lower().replace('-', ' ') not in s.lower().replace('-', ' '):
        s += DOT + title
    return s


def props(info, language=lambda code: code):
    """aeon.mi.* (without the prefix) -> text, for one file; language(code) names a language (ISO 639) for the screen"""
    if not info:
        return {}
    audio = info.get('audio') or []
    main = next((a for a in audio if a.get('default')), audio[0] if audio else None)
    commentary = [a for a in audio if 'commentary' in (a.get('title') or '').lower()]
    subs = info.get('subs') or []
    langs = []
    for s in subs:
        n = language(s['lang']) if s.get('lang') else ''
        if n and n not in langs:
            langs.append(n)
    video = [x for x in (info.get('vcodec'), info.get('vprofile') if info.get('vprofile') and info['vprofile'] != info.get('vcodec') else '',
                         ('%d-bit' % info['bitdepth']) if info.get('bitdepth') else '',
                         ('%g fps' % round(info['fps'], 3)) if info.get('fps') else '') if x]
    hdr = info.get('hdr') or ''
    if info.get('hybrid') and hdr == 'Dolby Vision':
        hdr = 'Dolby Vision + HDR10'
    return {
        'from': info.get('from') or '',
        'source': info.get('source') or '',
        'format': info.get('format') or '',
        'vsource': info.get('vsource') or '',
        'vcodec': info.get('vcodec') or '',
        'edition': info.get('edition') or '',
        'res': _res(info),
        'hdr': hdr,
        '3d': '3D' if info.get('three_d') else '',
        'video': DOT.join(video),
        'container': info.get('container') or '',
        'size': _size(info.get('size')),
        'bitrate': ('%.1f Mb/s' % info['mbps']) if info.get('mbps') else '',
        'audio': _audio_line(main, language) if main else '',
        'audio.count': str(len(audio)) if audio else '',
        'audio.list': '[CR]'.join(_audio_line(a, language) for a in audio),
        'commentary': str(len(commentary)) if commentary else '',
        'subs.count': str(len(subs)) if subs else '',
        'subs.langs': ', '.join(langs),
        'sdh': 'SDH' if any(s.get('sdh') for s in subs) else '',
        'chapters': str(info['chapters']) if info.get('chapters') else '',
    }
