# -*- coding: utf-8 -*-
"""Decisions of the context menu items (context.py). No Kodi imports."""

REFRESH = {'movie': ('VideoLibrary.RefreshMovie', 'movieid'),
           'episode': ('VideoLibrary.RefreshEpisode', 'episodeid'),
           'tvshow': ('VideoLibrary.RefreshTVShow', 'tvshowid'),
           'musicvideo': ('VideoLibrary.RefreshMusicVideo', 'musicvideoid')}
MUSIC = ('artist', 'album', 'song')
VIDEO = ('movie', 'set', 'tvshow', 'season', 'episode', 'musicvideo', 'video')


def refresh_call(dbtype, dbid):
    """(JSON-RPC method, params) that refreshes this library item, or None. Local .nfo files are read again
    (ignorenfo off), as Kodi's own Refresh does with a local scraper."""
    dbtype = (dbtype or '').strip().lower()
    dbid = str(dbid or '').strip()
    if dbtype not in REFRESH or not dbid.isdigit() or int(dbid) <= 0:
        return None
    method, key = REFRESH[dbtype]
    return method, {key: int(dbid), 'ignorenfo': False}


def refresh_progress(done, total):
    """Percent for the refresh toast: episodes done of the show's episodes; with no count (a film) a token 10."""
    if total <= 0:
        return 10
    return max(1, min(100, int(round(100.0 * done / total))))


def refresh_line(done, total, season=None, episode=None, title='', words=None):
    """Second line of the refresh toast: 'Episode 3 of 24: S01E03 Pilot', or 'Episode 3 of 24' before the name is known.
    words: the texts in Kodi's language ({'line': 'Episode %d of %d', 'reading': 'Reading the information'})."""
    words = words or {}
    if total <= 0:
        return title or words.get('reading') or 'Reading the information'
    line = (words.get('line') or 'Episode %d of %d') % (min(done, total), total)
    code = ''
    if season is not None and episode is not None and int(episode) > 0:
        code = 'S%02dE%02d' % (int(season), int(episode))
    name = ' '.join(part for part in (code, title or '') if part)
    return '%s: %s' % (line, name) if name else line


def refresh_finished(kind, events, total, idle_s, since_start_s):
    """Is the refresh job done? kind: the refreshed item's type; events: types of the VideoLibrary.OnUpdate
    notifications seen so far ('tvshow', 'episode', 'movie' ...); total: episodes asked for (0 = not refreshed).
    Done when every episode was updated, when the item itself was updated (no episodes asked), or after 20 s
    without news once something came; a hard stop after 2 minutes plus 10 s an episode."""
    episodes = sum(1 for e in events if e == 'episode')
    if total > 0 and episodes >= total:
        return True
    if total <= 0 and kind in events:
        return True
    if events and idle_s >= 20:
        return True
    return since_start_s >= 120 + 10 * max(0, total)


def library_for(dbtype, in_music, in_videos):
    """'music' / 'video' for Update / Clean library, '' when it cannot be told (Home, a menu item): then ask."""
    dbtype = (dbtype or '').strip().lower()
    if dbtype in MUSIC:
        return 'music'
    if dbtype in VIDEO:
        return 'video'
    if in_music:
        return 'music'
    if in_videos:
        return 'video'
    return ''


# ---- order and switches of the context items (Skin settings > Context menu) -------------------------------------
# Kodi lists an add-on's context items in addon.xml order, and that order cannot change at run time. So addon.xml has
# every item at every place (4 x 4): the one shown at place n is the item named by Skin.String(aeon.ctx.pos<n>).
ACTIONS = ('refresh', 'update', 'clean', 'shot')          # default order (all four strings empty)
# string ids of the labels (resources/language/.../strings.po: Refresh information, Update library, Clean library,
# Take screenshot); Kodi translates a numeric <label> of a context item from the add-on's own strings
LABELS = {'refresh': 32000, 'update': 32001, 'clean': 32002, 'shot': 32003}
# switch per item: (skin bool, True when the bool means "off")
SWITCH = {'refresh': ('aeon.ctx.refresh', False), 'update': ('aeon.ctx.update', False),
          'clean': ('aeon.ctx.clean', False), 'shot': ('aeon.ctx.noshot', True)}
APPLIES = {
    'refresh': '!ListItem.IsParentFolder + Integer.IsGreater(ListItem.DBID,0) + [String.IsEqual(ListItem.DBType,movie) | '
               'String.IsEqual(ListItem.DBType,tvshow) | String.IsEqual(ListItem.DBType,episode) | '
               'String.IsEqual(ListItem.DBType,musicvideo)]',
    'update': '[Window.IsActive(videos) | Window.IsActive(music) | Window.IsActive(home)]',
    'clean': '[Window.IsActive(videos) | Window.IsActive(music) | Window.IsActive(home)]',
    'shot': '',
}
FIRST_ROW = 9672          # the four rows of the settings page are 9672-9675


def read_order(values):
    """The four skin strings -> the order in use; anything that is not all four items once = the default."""
    got = [(v or '').strip().lower() for v in values]
    if sorted(got) == sorted(ACTIONS):
        return got
    return list(ACTIONS)


def moved(order, slot, delta):
    """(new order, new place) after moving the item at place slot (1-4) by delta; unchanged at the ends."""
    i, j = slot - 1, slot - 1 + delta
    if not (0 <= i < len(order) and 0 <= j < len(order)):
        return list(order), slot
    new = list(order)
    new[i], new[j] = new[j], new[i]
    return new, j + 1


def at_place(place, action):
    """Condition: place (1-4) holds action."""
    cond = 'String.IsEqual(Skin.String(aeon.ctx.pos%d),%s)' % (place, action)
    if ACTIONS[place - 1] == action:
        cond = '[%s | String.IsEmpty(Skin.String(aeon.ctx.pos1))]' % cond
    return cond


def is_on(action):
    setting, inverted = SWITCH[action]
    return ('!' if inverted else '') + 'Skin.HasSetting(%s)' % setting


def addon_items(indent='\t\t\t'):
    """The <item> elements of addon.xml's context menu, place by place."""
    out = []
    for place in range(1, len(ACTIONS) + 1):
        for action in ACTIONS:
            cond = ' + '.join(c for c in (at_place(place, action), is_on(action), APPLIES[action]) if c)
            # Kodi keeps only one context item per script + arguments (the label and the condition do not count), so
            # the place goes into the arguments; context.py reads the first one
            out.append('%s<item library="context.py" args="%s,%d">\n%s\t<label>%s</label>\n%s\t<visible>%s</visible>\n%s</item>'
                       % (indent, action, place, indent, LABELS[action], indent, cond, indent))
    return '\n'.join(out)
