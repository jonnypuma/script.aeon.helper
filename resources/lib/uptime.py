# -*- coding: utf-8 -*-
"""Short form of Kodi's uptime labels. No Kodi imports.

System.Uptime / System.TotalUptime read "8 Days, 15 Hours, 2 Minutes" in the user's language, too long for a narrow
panel. The numbers are always minutes, hours+minutes or days+hours+minutes, so only the numbers are read: this works
in every language."""
import re

UNITS = ('d', 'h', 'm')


def short(label):
    """'8 Days, 15 Hours, 2 Minutes' -> '8d 15h 2m'; '3 Hours, 4 Minutes' -> '3h 4m'; no numbers -> '', any other shape unchanged."""
    numbers = re.findall(r'\d+', label or '')
    if not numbers:
        return ''                    # 'Busy' while Kodi is still working it out: the skin shows Kodi's own text
    if not 1 <= len(numbers) <= 3:
        return label or ''
    units = UNITS[len(UNITS) - len(numbers):]
    return ' '.join('%d%s' % (int(number), unit) for number, unit in zip(numbers, units))
