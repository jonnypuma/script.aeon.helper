# -*- coding: utf-8 -*-
"""Skin settings > System > Recommended add-ons (0.3.114, skin 0.56.53; no Kodi imports): the optional add-ons that
give Aeon Fuse more to show, what each adds (a skin string id) and the repository it comes from (None: Kodi's own
repository). addonrec.py shows the list and installs. tests/test_recommended.py."""

# add-on id, name, skin string id of what it adds, repository id (None = Kodi repository)
ADDONS = [
    ('plugin.video.themoviedb.helper', 'TMDb Helper', 32702, None),
    ('script.karmamole.helper', 'KarmaMole Skin Helper', 32706, None),
    ('resource.images.studios.white', 'Studio Icons - White', 32709, None),
    ('resource.images.recordlabels.white', 'Record Label Icons - White', 32710, None),
    ('resource.images.languageflags.colour', 'Language Flags - Colour', 32711, None),
    ('resource.images.weathericons.white', 'Weather Icons - White', 32767, None),
    ('script.embuary.helper', 'Embuary Helper', 32703, None),
    ('script.cu.lrclyrics', 'CU LRC Lyrics', 32704, None),
    ('script.artistslideshow', 'Artist Slideshow', 32705, None),
    ('screensaver.aeon.fuse', 'Aeon Fuse Screensaver', 32712, 'repository.skippyrepo'),
    ('service.skippy', 'Skippy - Video Segment Skipper', 32707, 'repository.skippyrepo'),
    ('service.trickplay', 'Trickplay Preview', 32708, 'repository.skippyrepo'),
    ('script.tinyppi', 'TinyPPI', 32768, 'repository.jamal2362'),
    ('resource.fonts.copacetic', 'Copacetic Fonts (Inter)', 32769, None),
    ('resource.font.robotocjksc', 'Roboto CJKSC', 32770, 'repository.jamal2362'),
]

# Aeon Fuse Waveform Visualizer (0.3.115): one add-on per build, the right one for this device (platform.machine())
WAVE_NAME = 'Aeon Fuse Waveform Visualizer'
WAVE_STRING = 32797
WAVE_IDS = {'linux-arm64': 'visualization.aeonwave.linux-arm64', 'linux-armv7': 'visualization.aeonwave.linux-armv7',
            'linux-x86_64': 'visualization.aeonwave.linux-x86_64', 'windows-x64': 'visualization.aeonwave.windows-x64'}


def waveform_id(machine, system, android=False):
    """the visualizer add-on for this device, or None (no build: Android, macOS, iOS, 32-bit Windows, others).
    machine / system: platform.machine() / platform.system()"""
    if android:
        return None
    m = (machine or '').lower()
    sysname = (system or '').lower()
    if sysname == 'windows':
        return WAVE_IDS['windows-x64'] if m in ('amd64', 'x86_64') else None
    if sysname != 'linux':
        return None
    if m in ('aarch64', 'arm64'):
        return WAVE_IDS['linux-arm64']
    if m.startswith('armv7') or m.startswith('armv8l'):
        return WAVE_IDS['linux-armv7']
    if m in ('x86_64', 'amd64'):
        return WAVE_IDS['linux-x86_64']
    return None


def listed(machine=None, system=None, android=False):
    """ADDONS with the visualizer for this device after the Aeon Fuse Screensaver (left out where there is no build)"""
    wave = waveform_id(machine, system, android)
    if not wave:
        return list(ADDONS)
    out = []
    for item in ADDONS:
        out.append(item)
        if item[0] == 'screensaver.aeon.fuse':
            out.append((wave, WAVE_NAME, WAVE_STRING, 'repository.skippyrepo'))
    return out


# repository id -> (name, zip address) - the same as README.md, "Repositories"
REPOS = {
    'repository.skippyrepo': ('Skippy Repo', 'https://raw.githubusercontent.com/jonnypuma/repository.skippyrepo/main/'
                                             'zips/repository.skippyrepo/repository.skippyrepo-1.0.4.zip'),
    'repository.jamal2362': ('jamal2362', 'https://raw.githubusercontent.com/CE-Repo/repository.jamal2362/main/addons/'
                                          'zips/repository.jamal2362/repository.jamal2362-4.0.zip'),
}


def rows(has_addon, version=None, items=None):
    """[(addon id, name, string id, installed, version, repository needed first or None)] in list order.
    has_addon(id) -> bool; version(id) -> str or ''"""
    out = []
    for aid, name, sid, repo in (items if items is not None else ADDONS):
        inst = bool(has_addon(aid))
        need = repo if (repo and not inst and not has_addon(repo)) else None
        out.append((aid, name, sid, inst, (version(aid) if (inst and version) else ''), need))
    return out


def count(has_addon, items=None):
    """(installed, all)"""
    items = items if items is not None else ADDONS
    return sum(1 for a in items if has_addon(a[0])), len(items)


def zip_ok(names, repo):
    """a repository zip holds exactly one top folder, named after the repository, and nothing outside it"""
    tops = set(n.split('/', 1)[0] for n in names if n)
    return tops == {repo} and not any(n.startswith('/') or '..' in n.split('/') for n in names)
