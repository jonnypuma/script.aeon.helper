# -*- coding: utf-8 -*-
"""Backdrop pool for the settings screens (skin 0.32.0): fanart seen on Home (spotlights and strips) plus a few random
library titles, newest first, no repeats; a new random one each time a settings screen opens. No Kodi imports."""
import random

LIMIT = 40


def add(pool, art, limit=LIMIT):
    """Pool with art on top (moved there when it was already in); blank or non-picture paths change nothing."""
    art = (art or '').strip()
    if not art or art.startswith('DefaultVideo') or art.endswith('.xbt'):
        return list(pool)
    return ([art] + [a for a in pool if a != art])[:limit]


def pick(pool, current='', rng=random):
    """A random backdrop from the pool, not the one on screen now when there is a choice ('' for an empty pool)."""
    choices = [a for a in pool if a != current] or list(pool)
    return rng.choice(choices) if choices else ''
