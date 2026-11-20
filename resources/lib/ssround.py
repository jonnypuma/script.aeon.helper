# -*- coding: utf-8 -*-
"""One round of the Aeon Fuse screensaver (screensaver.aeon.fuse 1.3.0, skin 0.56.22; no Kodi imports).

The user: "every item displayed is one dot in the sequence and it does 10 items at a time or whatever the user has set
it to and then it just goes back to the first dot and does 10 random more from the sources the user has set to use".
So a round is one list of N items drawn at random from all the switched-on sources (films, shows, albums, in the
cinemas now, airing today, airing tomorrow), mixed, each dot one item; the next round is N new ones."""
import random

KINDS = ('movies', 'tvshows', 'music', 'cinema', 'today', 'tomorrow')
MIN_COUNT, MAX_COUNT, DEFAULT_COUNT = 3, 10, 10


def kinds_of(text):
    """'movies,today,bogus' -> ['movies', 'today'] in the usual order; nothing usable -> ['movies']."""
    asked = set((text or '').replace(' ', '').split(','))
    out = [k for k in KINDS if k in asked]
    return out or ['movies']


def count_of(text):
    try:
        n = int(text)
    except (TypeError, ValueError):
        return DEFAULT_COUNT
    return max(MIN_COUNT, min(MAX_COUNT, n))


def mix(pools, count, rng=None):
    """[(kind, item)] of up to count items: each slot takes a source at random among those with items left, avoiding
    the source of the slot before when another one has items; within a source the items keep their (random) order.
    pools: {kind: [items]} (already random, at most count each)."""
    rng = rng or random.Random()
    left = dict((k, list(v)) for k, v in pools.items() if v)
    out = []
    last = None
    while left and len(out) < count:
        kinds = sorted(left)
        others = [k for k in kinds if k != last]
        kind = rng.choice(others or kinds)
        out.append((kind, left[kind].pop(0)))
        if not left[kind]:
            del left[kind]
        last = kind
    return out
