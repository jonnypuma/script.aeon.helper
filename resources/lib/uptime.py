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


def from_seconds(seconds):
    """3725 -> '1h 2m'; 1800000 -> '20d 20h 0m'; under a minute -> '0m'. Same shape as short()."""
    if seconds is None or seconds < 0:
        return ''
    minutes = int(seconds // 60)
    days, minutes = divmod(minutes, 1440)
    hours, minutes = divmod(minutes, 60)
    if days:
        return '%dd %dh %dm' % (days, hours, minutes)
    if hours:
        return '%dh %dm' % (hours, minutes)
    return '%dm' % minutes


def system_seconds():
    """How long the machine (not Kodi) has been on, in seconds, or None: /proc/uptime on Linux / CoreELEC / Android,
    GetTickCount64 on Windows."""
    try:
        with open('/proc/uptime') as handle:
            return float(handle.read().split()[0])
    except (IOError, OSError, ValueError, IndexError):
        pass
    try:
        import ctypes
        tick = ctypes.windll.kernel32.GetTickCount64
        tick.restype = ctypes.c_ulonglong
        return tick() / 1000.0
    except Exception:
        return None


def number(label):
    """First number in a Kodi label ('58%', '2153MB', '46°C', 'Busy') or None."""
    found = re.search(r'\d+(?:[.,]\d+)?', label or '')
    return float(found.group(0).replace(',', '.')) if found else None


def celsius(label):
    value = number(label)
    if value is None:
        return None
    return (value - 32) * 5 / 9 if 'F' in (label or '') else value


def health(mem_pct, mem_used, mem_total, cpu_temp, gpu_temp):
    """Labels as Kodi gives them -> (status, memory percent text, memory text).
    status: 'memory' (90 % or more in use), 'warm' (CPU 75 °C / GPU 80 °C or more), else 'good'."""
    pct = number(mem_pct)
    used, total = number(mem_used), number(mem_total)
    cpu, gpu = celsius(cpu_temp), celsius(gpu_temp)
    if pct is not None and pct >= 90:
        status = 'memory'
    elif (cpu is not None and cpu >= 75) or (gpu is not None and gpu >= 80):
        status = 'warm'
    else:
        status = 'good'
    pct_text = str(int(round(pct))) if pct is not None else ''
    mem_text = '%.1f / %.1f GB' % (used / 1024, total / 1024) if used and total else ''
    return status, pct_text, mem_text
