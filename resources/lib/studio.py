# -*- coding: utf-8 -*-
"""Studio / network logos (resource.images.studios.white) are named after one studio, but Kodi joins all of a
title's studios into ListItem.Studio ("Carnival Films / BBC Film / Heyday Films"): no file has that name, so no
logo showed. The service publishes the first one. No Kodi imports."""


def first(studios):
    """The first studio of Kodi's joined list ('A / B / C' -> 'A'); '' for none."""
    for part in (studios or '').split(' / '):
        part = part.strip()
        if part:
            return part
    return ''


def xbt_names(path):
    """The lower-case file names in a Kodi texture pack (resource.images.studios.white's Textures.xbt): only the index
    at its head is read (name, then the frames' records of 40 bytes each)."""
    import struct
    names = set()
    with open(path, 'rb') as handle:
        if handle.read(4) != b'XBTF':
            return names
        handle.read(1)
        count, = struct.unpack('<I', handle.read(4))
        for _ in range(count):
            name = handle.read(256).split(b'\0')[0].decode('utf-8', 'replace').lower()
            _loop, frames = struct.unpack('<II', handle.read(8))
            handle.seek(frames * 40, 1)
            names.add(name)
    return names


def pick(studios, names):
    """(logo, text) for Kodi's joined studios (skin 0.56.11; the user: "just use one if this movie doesn't have one"):
    the first studio that has a logo in the pack, else no logo and the first studio's name for the skin to show as
    text. names None (no pack to read): the first studio, as before."""
    parts = [part.strip() for part in (studios or '').split(' / ') if part.strip()]
    if not parts:
        return '', ''
    if names is None:
        return parts[0], ''
    for part in parts:
        if part.lower() + '.png' in names:
            return part, ''
    return '', parts[0]
