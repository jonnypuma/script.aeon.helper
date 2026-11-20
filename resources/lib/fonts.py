# -*- coding: utf-8 -*-
"""Per-section fonts for the Aeon Fuse skin. Pure text work, no Kodi imports.

Kodi can only switch a whole font set. To let Home, the library, the headings, the settings pages and the player each
use their own family, the skin's XML uses section font names (hm_ui_24_bold, lb_ui_24_bold ...) and Font.xml defines
them. In every font set a section name is a copy of the plain name, taken either from that same font set (section
follows the font set) or from the font set the user picked for the section.

build() is idempotent: it removes the block it wrote earlier and writes a new one."""
import re

# section key -> prefix of its font names
SECTIONS = (('home', 'hm_'), ('library', 'lb_'), ('headings', 'hd_'), ('settings', 'st_'), ('player', 'pl_'))
PREFIX = dict(SECTIONS)
HEADING = ('display_', 'serif_', 'font45_title')     # the Home menu labels (aeon_title_) belong to Home
# families that are one file: every weight of the section uses it, sizes stay those of the font set
MCF = 'special://home/addons/script.mcfontface/resources/'
EXTRA = (('Aeon Serif', 'AeonSerif-Medium.ttf'), ('Aeon Display', 'AeonDisplay-Medium.ttf'),
         ('Source Sans 3 (one weight)', MCF + 'SourceSans3.ttf'), ('PT Sans', MCF + 'PTSans-Regular.ttf'), ('Hind', MCF + 'Hind-Regular.ttf'),
         ('Noto Sans', MCF + 'NotoSans-Regular.ttf'), ('DejaVu Sans', MCF + 'DejaVuSans.ttf'), ('Noto Mono', MCF + 'NotoMono-Regular.ttf'),
         # heading faces (0.37.0): one weight each, the one the user picked on the choices page; kept last so the
         # preview numbers of the families above do not move
         ('Fraunces Bold', 'Fraunces-Bold.ttf'), ('Bebas Neue', 'BebasNeue-Regular.ttf'),
         ('Oswald SemiBold', 'Oswald-SemiBold.ttf'), ('Barlow Condensed Bold', 'BarlowCondensed-Bold.ttf'),
         # 0.38.0: the heading faces of the new pairings (Gnomon is a variable font: Kodi draws its default instance)
         ('Funnel Display ExtraBold', 'FunnelDisplay-ExtraBold.ttf'), ('Cal Sans SemiBold', 'CalSans-SemiBold.ttf'),
         ('Hubot Sans Condensed ExtraBold', 'HubotSansCondensed-ExtraBold.ttf'),
         ('Hubot Sans Expanded Bold', 'HubotSansExpanded-Bold.ttf'), ('Saira Condensed Bold', 'SairaCondensed-Bold.ttf'),
         ('Clarity City Bold', 'ClarityCity-Bold.ttf'), ('Gnomon', 'Gnomon-Simple.ttf'),
         ('LT Superior Serif Bold', 'LTSuperiorSerif-Bold.otf'), ('LT Veritas Condensed Bold', 'LTVeritas-BoldCondensed.ttf'),
         ('Cooper Hewitt Heavy', 'CooperHewitt-Heavy.otf'), ('TASA Explorer ExtraBold', 'TASAExplorer-ExtraBold.ttf'))
ONEFILE = dict(EXTRA)
# font combinations (0.37.0): (key, name, family for the headings, family for every other section; '' = font set)
PRESETS = (('figtree', 'Figtree', '', ''),
           ('fraunces', 'Fraunces + Figtree', 'Fraunces Bold', ''),
           ('bebas', 'Bebas Neue + Figtree', 'Bebas Neue', ''),
           ('oswald', 'Oswald + Source Sans 3', 'Oswald SemiBold', 'Source Sans 3 (cut)'),
           ('barlowc', 'Barlow Condensed + Barlow', 'Barlow Condensed Bold', 'Barlow'),
           # 0.38.0: the pairings from the font page
           ('funnel', 'Funnel Display + Figtree', 'Funnel Display ExtraBold', ''),
           ('calsans', 'Cal Sans + Figtree', 'Cal Sans SemiBold', ''),
           ('hubotc', 'Hubot Sans Condensed + Hubot Sans', 'Hubot Sans Condensed ExtraBold', 'Hubot Sans'),
           ('hubote', 'Hubot Sans Expanded + Figtree', 'Hubot Sans Expanded Bold', ''),
           ('sairac', 'Saira Condensed + Saira', 'Saira Condensed Bold', 'Saira'),
           ('clarity', 'Clarity City + Pretendard', 'Clarity City Bold', 'Pretendard'),
           ('gnomon', 'Gnomon + Clarity City', 'Gnomon', 'Clarity City'),
           ('ltserif', 'LT Superior Serif + LT Superior', 'LT Superior Serif Bold', 'LT Superior'),
           ('veritas', 'LT Veritas Condensed + LT Veritas', 'LT Veritas Condensed Bold', 'LT Veritas'),
           ('cooper', 'Cooper Hewitt Heavy + Cooper Hewitt', 'Cooper Hewitt Heavy', 'Cooper Hewitt'),
           ('bebasclarity', 'Bebas Neue + Clarity City', 'Bebas Neue', 'Clarity City'),
           ('frauncesronzino', 'Fraunces + Ronzino', 'Fraunces Bold', 'Ronzino'),
           ('oswaldpret', 'Oswald + Pretendard', 'Oswald SemiBold', 'Pretendard'),
           ('tasa', 'TASA Explorer + Figtree', 'TASA Explorer ExtraBold', ''))


def preset_choices(heading, body):
    """Section choices of a combination: the heading family for Headings, the text family everywhere else."""
    return dict((key, heading if key == 'headings' else body) for key, _prefix in SECTIONS)


def preset_of(choices):
    """Key of the combination these choices are, or '' when they are a mix of the user's own."""
    now = dict((key, (choices or {}).get(key) or '') for key, _prefix in SECTIONS)
    for key, _name, heading, body in PRESETS:
        if preset_choices(heading, body) == now:
            return key
    return ''
# families with the four weights the skin uses, as files in the skin's fonts folder: <pattern> % weight, or the four
# file names (Regular, Medium, SemiBold, Bold) when the files are named otherwise or a weight is missing.
# The weight of a font name is the weight the Default font set (Figtree) gives it.
WEIGHTS = ('Regular', 'Medium', 'SemiBold', 'Bold')
WEIGHTED = (('Barlow', 'Barlow-%s.ttf'), ('Montserrat', 'Montserrat-%s.ttf'), ('Manrope', 'Manrope-%s.ttf'),
            ('IBM Plex Sans (cut)', 'AeonPSans-%s.ttf'), ('Source Sans 3 (cut)', 'AeonSSans-%s.ttf'),
            ('Source Serif 4 (cut)', 'AeonSSerif-%s.ttf'),
            # 0.38.0: the text faces of the new pairings
            ('Hubot Sans', 'HubotSans-%s.ttf'), ('Saira', 'Saira-%s.ttf'), ('Pretendard', 'PretendardStd-%s.ttf'),
            ('Clarity City', 'ClarityCity-%s.ttf'), ('LT Superior', 'LTSuperior-%s.otf'),
            ('LT Veritas', ('LTVeritas-Regular.ttf', 'LTVeritas-Medium.ttf', 'LTVeritas-Medium.ttf', 'LTVeritas-Bold.ttf')),
            ('Cooper Hewitt', ('CooperHewitt-Book.otf', 'CooperHewitt-Medium.otf', 'CooperHewitt-Semibold.otf', 'CooperHewitt-Bold.otf')),
            ('Ronzino', ('Ronzino-Regular.otf', 'Ronzino-Medium.otf', 'Ronzino-Medium.otf', 'Ronzino-Bold.otf')))
PATTERN = dict(WEIGHTED)
REFERENCE = 'Default'
_WEIGHT = re.compile(r'<filename>[^<]*-(Regular|Medium|SemiBold|Bold)\.ttf</filename>')


def weight_file(family, weight):
    pattern = PATTERN[family]
    if isinstance(pattern, tuple):
        return pattern[WEIGHTS.index(weight)]
    return pattern % weight


def weighted_files(family):
    return [weight_file(family, weight) for weight in WEIGHTS]
# the picker shows a mock-up in the focused family: pv<n>_<key> is that family at the size of a plain font
# (n = 0 follows the font set, n = 1.. is the position in families()). The mock-up draws its title in family h and
# the rest in family b, so a combination shows both of its fonts (a single family: h = b).
PREVIEW = (('h', 'display_48'), ('t', 'ui_28_bold'), ('b', 'body_24'), ('s', 'small_20_bold'), ('c', 'cap_20'))
SKIP = ('lyr',)                      # the animated lyrics keep their own display faces
BEGIN = '<!-- sections:begin (written by script.aeon.helper, do not edit) -->'
END = '<!-- sections:end -->'
MARK = re.compile(r'<!-- aeon-fonts: (.*?) -->')
# 0.3.106 (skin 0.56.31): capitals twins uc_st_<name> of these settings fonts, the settings face with style uppercase.
# The Fused Glass style draws its settings lists in capitals; Kodi's own rows get their text from Kodi, so only a
# font can capitalise them. Written inside the generated block so they follow the settings font choice.
CAPS = ('ui_24', 'ui_24_semibold', 'ui_24_bold', 'ui_22_semibold', 'ui_22_bold', 'small_20_semibold')

_MARKLINE = re.compile(r'<!-- aeon-fonts: .*? -->\n?')
_SET = re.compile(r'(<fontset\b[^>]*>)(.*?)(</fontset>)', re.S)
_FONT = re.compile(r'<font>\s*<name>([^<]+)</name>(.*?)</font>', re.S)
_FILE = re.compile(r'<filename>[^<]*</filename>')
_BLOCK = re.compile(r'[ \t]*' + re.escape(BEGIN) + r'.*?' + re.escape(END) + r'\n?', re.S)


def is_heading(name):
    return name.startswith(HEADING)


def is_skipped(name):
    return name.startswith(SKIP)


def section_name(name, section):
    """Font name a control of that section uses. Outside the sections only the heading faces get a name of their own."""
    if is_skipped(name) or name.startswith('$'):
        return name
    if section in PREFIX and section != 'headings':
        return PREFIX[section] + name
    if is_heading(name):
        return PREFIX['headings'] + name
    return name


def strip(text):
    """Font.xml without the generated block and marker."""
    return _MARKLINE.sub('', _BLOCK.sub('', text))


def fontsets(text):
    """{font set id: {font name: rest of the <font> element}} in file order (plain names only)."""
    out = {}
    for head, body, _tail in _SET.findall(strip(text)):
        ident = re.search(r'\bid="([^"]*)"', head)
        if not ident:
            continue
        fonts = {}
        for name, rest in _FONT.findall(body):
            fonts.setdefault(name.strip(), ' '.join(rest.split()).replace('> <', '><'))
        out[ident.group(1)] = fonts
    return out


def files(text):
    """{font set id: sorted file names it needs}, lyrics faces left out."""
    out = {}
    for ident, fonts in fontsets(text).items():
        names = set()
        for name, rest in fonts.items():
            if is_skipped(name):
                continue
            names.update(re.findall(r'<filename>([^<]*)</filename>', rest))
        out[ident] = sorted(names)
    return out


def families(text):
    """Every family the skin knows, in a fixed order: the font sets, then the one-file families."""
    return list(fontsets(text)) + [name for name, _pattern in WEIGHTED] + [name for name, _path in EXTRA]


def family_font(family, name, own, sets):
    """Rest of the <font> element for that plain font name in that family ('' = the font set itself)."""
    if family in PATTERN:
        reference = (sets.get(REFERENCE) or own).get(name) or own[name]
        found = _WEIGHT.search(reference)
        weight = found.group(1) if found else 'Regular'
        return _FILE.sub(lambda m: '<filename>%s</filename>' % weight_file(family, weight), reference)
    if family in ONEFILE:
        return _FILE.sub(lambda m: '<filename>%s</filename>' % ONEFILE[family], own[name])
    return (sets.get(family) or own).get(name) or own[name]


def has_bold(family, sets):
    """True when the family draws bold text with another file than normal text (a real bold face)."""
    if family in PATTERN:
        return True
    fonts_ = sets.get(family)
    if not fonts_:
        return False
    names = lambda key: _FILE.findall(fonts_.get(key, ''))
    bold = names('ui_24_bold')
    return bool(bold) and bold != (names('ui_24') or names('body_24'))


def uppercase(rest):
    """Rest of a <font> element with style uppercase added to its own style."""
    if '<style>' in rest:
        return re.sub(r'<style>([^<]*)</style>', lambda m: '<style>%s uppercase</style>' % m.group(1).strip(), rest, count=1)
    return rest + '<style>uppercase</style>'


def clean(choices, sets):
    """Only known sections, only font sets that exist; '' = follow the font set."""
    out = {}
    for key, _prefix in SECTIONS:
        value = (choices or {}).get(key) or ''
        out[key] = value if (value in sets or value in ONEFILE or value in PATTERN) else ''
    return out


def marker(choices):
    return ';'.join('%s=%s' % (key, choices.get(key) or '') for key, _p in SECTIONS)


def read_marker(text):
    """Choices the file was built with, or None when it has never been built."""
    found = MARK.search(text)
    if not found:
        return None
    out = {}
    for part in found.group(1).split(';'):
        key, _sep, value = part.partition('=')
        out[key] = value
    return out


def build(text, choices):
    """Font.xml with the section fonts of every font set written for these choices."""
    base = strip(text)
    sets = fontsets(base)
    choices = clean(choices, sets)
    known = families(base)

    def one(match):
        head, body, tail = match.groups()
        ident = re.search(r'\bid="([^"]*)"', head)
        own = sets.get(ident.group(1), {}) if ident else {}
        lines = ['\t\t' + BEGIN]
        for key, prefix in SECTIONS:
            for name in own:
                if is_skipped(name) or (key == 'headings' and not is_heading(name)):
                    continue
                # a heading face follows its own section, unless a family is chosen for Headings: that one wins everywhere
                family = (choices['headings'] or choices[key]) if is_heading(name) else choices[key]
                rest = family_font(family, name, own, sets)
                lines.append('\t\t<font><name>%s%s</name>%s</font>' % (prefix, name, rest))
        for name in CAPS:
            if name in own:
                rest = uppercase(family_font(choices['settings'], name, own, sets))
                lines.append('\t\t<font><name>uc_%s%s</name>%s</font>' % (PREFIX['settings'], name, rest))
        for number, family in enumerate([''] + known):
            for key, name in PREVIEW:
                if name in own:
                    lines.append('\t\t<font><name>pv%d_%s</name>%s</font>' % (number, key, family_font(family, name, own, sets)))
        lines.append('\t\t' + END)
        return head + body.rstrip('\t ') + '\n'.join(lines) + '\n\t' + tail

    out = _SET.sub(one, base)
    note = '<!-- aeon-fonts: %s -->' % marker(choices)
    if '<fonts>' in out:
        out = out.replace('<fonts>', note + '\n<fonts>', 1)
    return out
