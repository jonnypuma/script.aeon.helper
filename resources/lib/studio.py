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
