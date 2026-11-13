# -*- coding: utf-8 -*-
"""Recent searches of the skin's Search window: newest first, no repeats (case ignored), at most LIMIT. No Kodi imports."""

LIMIT = 8


def clean(query):
    """The query as it is kept: inner runs of spaces folded, ends trimmed."""
    return ' '.join((query or '').split())


def add(history, query, limit=LIMIT):
    """History with the query on top (an earlier copy of it removed). A blank query changes nothing."""
    query = clean(query)
    if not query:
        return list(history)
    rest = [q for q in history if q.lower() != query.lower()]
    return ([query] + rest)[:limit]


def remove(history, index):
    """History without the entry at index (0-based); out of range changes nothing."""
    if 0 <= index < len(history):
        return history[:index] + history[index + 1:]
    return list(history)
