# -*- coding: utf-8 -*-
"""Colours for the palette picker: each palette's own row colours, with readable text.

A palette file (the skin's colors/<name>.xml) only lists what differs from colors/defaults.xml. The picker draws each
row like that palette's menus: an unfocused row on its panel colour with its accent ink, the focused row on its focus
bar with its bar ink. Text that would not stand out enough (WCAG contrast below 4.5) is moved towards white or black."""
import re

COLOUR = re.compile(r'<color\s+name="([^"]+)"\s*>\s*([0-9a-fA-F]{8})\s*</color>')


def parse(text):
    return dict((name, value.lower()) for name, value in COLOUR.findall(text or ''))


def rgb(argb):
    value = (argb or 'ff000000')[-6:]
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def luminance(argb):
    def channel(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb(argb))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def readable(ink, ground, needed=4.5):
    """ink, or ink blended towards white / black (whichever the ground needs) until it reads on ground."""
    if contrast(ink, ground) >= needed:
        return ink
    target = (255, 255, 255) if luminance(ground) < 0.5 else (0, 0, 0)
    r, g, b = rgb(ink)
    for step in range(1, 11):
        k = step / 10.0
        mixed = 'ff%02x%02x%02x' % tuple(int(round(c + (t - c) * k)) for c, t in zip((r, g, b), target))
        if contrast(mixed, ground) >= needed:
            return mixed
    return 'ff%02x%02x%02x' % target


def style(defaults, palette):
    """Row colours of one palette: ground / ink of an unfocused row, bar / bar ink of the focused one, the swatch."""
    c = dict(defaults)
    c.update(palette)
    ground = c.get('x_panel', 'ff303030')
    bar = c.get('aeon_white', 'ffe9e9e9')
    accent = c.get('aeon_accent', 'ffffffff')
    return {'ground': ground, 'ink': readable(accent, ground), 'bar': bar, 'barink': readable(c.get('aeon_onbar', 'ff1a1a1a'), bar),
            'swatch': accent}
