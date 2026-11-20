# -*- coding: utf-8 -*-
"""Short texts for the Fused Glass Home > System page (0.3.73). No Kodi imports: the service passes Kodi's labels in.

Kodi's own labels are long or shaped for a settings page ("22.0-RC2", "CoreELEC (official): 22.0-Piers_nightly_20261113",
"3840x2160 @ 24.00 Hz - Full screen", "#0:  18% #1: 100% ..."); the page wants "Kodi 22", "CoreELEC 22 Piers nightly,
13 November", "2160p · 24 Hz", "38%" and library numbers with a thousands separator."""
import re

# thousands separator per interface language (ISO 639-1); others use a no-break space
COMMA = ('en', 'ja', 'ko', 'zh', 'he', 'th')
DOT = ('de', 'nl', 'da', 'es', 'it', 'pt', 'el', 'tr', 'id', 'hr', 'sl', 'ro')


def major(version_short):
    """'22.0-RC2' -> ('22', 'RC2'); '21.2' -> ('21', ''); '' -> ('', '')."""
    found = re.match(r'\s*(\d+)(?:\.\d+)*(?:[-\s]+(.+))?', version_short or '')
    if not found:
        return '', ''
    return found.group(1), (found.group(2) or '').strip()


def device(friendly_name):
    """'Kodi (CoreELECAM9Pro)' -> 'CoreELECAM9Pro'; a name without brackets is returned as it is."""
    found = re.search(r'\(([^()]+)\)\s*$', friendly_name or '')
    return (found.group(1) if found else (friendly_name or '')).strip()


def os_line(info, months=None):
    """System.OSVersionInfo -> (short OS name, one line about it).
    'CoreELEC (official): 22.0-Piers_nightly_20261113' -> ('CoreELEC', 'CoreELEC 22 Piers nightly, 13 November')
    'LibreELEC (official): 12.0.1' -> ('LibreELEC', 'LibreELEC 12.0.1')
    'Windows 11, 64-bit Home (version 10.0 build 26200)' -> ('Windows', the same text)
    months: the twelve month names in the user's language (default English)."""
    info = (info or '').strip()
    if not info:
        return '', ''
    elec = re.match(r'(\w+ELEC)\b[^:]*:\s*(.*)$', info)
    if not elec:
        name = re.split(r'[\s,(]', info, 1)[0]
        return name, info
    name, rest = elec.group(1), elec.group(2).strip()
    version = re.match(r'(\d+)\.0-(.+)$', rest)
    if not version:
        return name, ('%s %s' % (name, rest)).strip()
    number, tail = version.group(1), version.group(2)
    stamp = re.search(r'_?(\d{4})(\d{2})(\d{2})$', tail)
    words = tail[:stamp.start()] if stamp else tail
    words = words.replace('_', ' ').strip()
    line = '%s %s %s' % (name, number, words) if words else '%s %s' % (name, number)
    if stamp:
        month = int(stamp.group(2))
        names = months or ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                           'October', 'November', 'December')
        if 1 <= month <= 12:
            line += ', %d %s' % (int(stamp.group(3)), names[month - 1])
    return name, line


def screen(label):
    """'3840x2160 @ 24.00 Hz - Full screen' -> '2160p · 24 Hz'; 23.976 Hz -> '23.98 Hz'; anything else unchanged."""
    found = re.match(r'\s*(\d+)\s*x\s*(\d+)(?:\s*@\s*([\d.,]+)\s*Hz)?', label or '')
    if not found:
        return label or ''
    text = '%sp' % found.group(2)
    if found.group(3):
        hz = float(found.group(3).replace(',', '.'))
        text += u' · %s Hz' % (('%d' % round(hz)) if abs(hz - round(hz)) < 0.005 else ('%.2f' % hz).rstrip('0'))
    return text


def cpu_average(label):
    """System.CPUUsage: '#0:  18% #1: 100% #2:  21% #3:  14%' (Linux, per core) or '13%' -> '38' / '13'; '' when
    there is no number."""
    numbers = [float(n.replace(',', '.')) for n in re.findall(r'(\d+(?:[.,]\d+)?)\s*%', label or '')]
    if not numbers:
        return ''
    return '%d' % round(sum(numbers) / len(numbers))


def grouped(value, language='en'):
    """6123 -> '6,123' (English), '6.123' (German / Dutch ...), '6 123' with a no-break space (French, Swedish ...)."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return '' if value is None else str(value)
    text = '{:,}'.format(number)
    lang = (language or 'en')[:2].lower()
    if lang in COMMA:
        return text
    return text.replace(',', '.' if lang in DOT else u' ')
