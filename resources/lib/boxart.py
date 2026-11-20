# -*- coding: utf-8 -*-
"""Which picture of the focused item gives the library page its colour (Backdrop = Colors) and the boxes theirs.
The picture the view shows: an episode its own thumbnail (every episode of a show shares the show's poster, so the
page never changed colour from one episode to the next), everything else its poster, an album its cover.
No Kodi imports."""

EPISODE = ('thumb', 'season.poster', 'tvshow.poster', 'poster')
DEFAULT = ('poster', 'tvshow.poster', 'thumb', 'album.thumb')
# Backdrop = Colors: the page colour comes from the picture on screen (0.3.55: no longer from the hidden fanart, which
# gave an artist with a black-and-white photo a maroon page)


def art_keys(dbtype):
    """ListItem.Art keys to try, in order, for an item of this ListItem.DBType."""
    return EPISODE if (dbtype or '').strip().lower() == 'episode' else DEFAULT


# Home spotlights: the menu item in focus (Container(9000).ListItem.Label2) -> the list that shows its spotlight
SPOT_LISTS = {'movies': 9421, 'tv': 9422, 'music': 9423, 'custom1': 9411, 'custom2': 9412, 'custom3': 9413, 'planner': 9414,
              # custom items 4-10 (0.3.86)
              'custom4': 9415, 'custom5': 9416, 'custom6': 9417, 'custom7': 9418, 'custom8': 9419, 'custom9': 9420,
              'custom10': 9424}


def spot_list(menu_key):
    """Id of the spotlight list on screen for this Home menu item, or 0."""
    return SPOT_LISTS.get((menu_key or '').strip().lower(), 0)


# the widget screens (dialog 1157): one full-screen list per page
WIDGET_LISTS = ('9401', '9402', '9403', '9404', '9405', '9406')


def is_widget_list(control_id):
    """True for the id of a widget screen page list."""
    return str(control_id or '').strip() in WIDGET_LISTS
