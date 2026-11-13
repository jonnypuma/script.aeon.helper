# -*- coding: utf-8 -*-
"""Headers in the Aeon Fuse style: 'Random shows' -> 'Random [B]shows[/B]' (the skin puts it in upper case).
No Kodi imports."""
import re

TAGS = re.compile(r'\[/?(?:B|I|UPPERCASE|LOWERCASE|CAPITALIZE|LIGHT)\]|\[COLOR [^\]]*\]|\[/COLOR\]', re.I)


def bold_last(label):
    """The label with its last word in bold; one word is all bold; empty stays empty. Kodi's own tags are dropped."""
    text = ' '.join(TAGS.sub('', label or '').split())
    if not text:
        return ''
    lead, _, last = text.rpartition(' ')
    return ('%s [B]%s[/B]' % (lead, last)) if lead else '[B]%s[/B]' % last
