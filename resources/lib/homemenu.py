# -*- coding: utf-8 -*-
"""Home menu positions (0.3.86): 24 positions, 10 custom items, and where Add item puts a new one. No Kodi calls."""

COUNT = 24                  # positions: the 14 presets and the 10 custom items all fit at once
CUSTOMS = 10
ADD_ROW = 9639              # Skin settings > Home menu: the Add item row
# Skin settings > Home menu: the row of each position (1-10: 9590-9599, 11-13: 9613-9615, 14-24: free ids after them)
ROWS = dict([(n, 9589 + n) for n in range(1, 11)] + [(11, 9613), (12, 9614), (13, 9615)] +
            list(zip(range(14, 25), (9627, 9628, 9629, 9631, 9632, 9633, 9634, 9635, 9636, 9637, 9638))))


def row_id(n):
    return ROWS.get(n, 0)


def custom_keys():
    return ['custom%d' % k for k in range(1, CUSTOMS + 1)]


def custom_number(key):
    """'custom10' -> '10' (the CustomMenu.<n>.* skin strings); '' for anything else"""
    return key[6:] if key.startswith('custom') and key[6:].isdigit() else ''


def used(value):
    return value not in ('', 'off')


def used_count(positions):
    return sum(1 for value in positions if used(value))


def add_target(positions):
    """The position Add item fills (1-based): the first empty one after the last item, else the first empty one
    anywhere, else 0 (the menu is full)."""
    last = max([n for n, value in enumerate(positions, 1) if used(value)] or [0])
    for n in range(last + 1, len(positions) + 1):
        if not used(positions[n - 1]):
            return n
    for n, value in enumerate(positions, 1):
        if not used(value):
            return n
    return 0


def is_tail(positions, n):
    """True when position n and every one after it are empty: its row hides in the editor"""
    return not any(used(value) for value in positions[n - 1:])


def remove(positions, hidden, n):
    """Delete (0.3.115): position n's item leaves the menu and the ones below it move up one place; the last position
    becomes empty. positions / hidden: lists in position order. Returns the new (positions, hidden)."""
    if not 1 <= n <= len(positions):
        return list(positions), list(hidden)
    pos = list(positions[:n - 1]) + list(positions[n:]) + ['off']
    hid = list(hidden[:n - 1]) + list(hidden[n:]) + [False]
    return pos, hid


def changed(old, new):
    """The 1-based places where two position (or flag) lists differ: only those are written back."""
    return [i for i, (a, b) in enumerate(zip(old, new), 1) if a != b]
