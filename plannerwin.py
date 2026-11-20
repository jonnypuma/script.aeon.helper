# -*- coding: utf-8 -*-
"""The Planner window of the Aeon Fuse skin (Custom_1168_Planner.xml): which day and week it shows.

RunScript(script.aeon.helper,planner,<command>) - the skin only draws; every move goes through here, so a move never
lands on an empty list and never goes back before today.

  init                 window opened: today, in the view used last time; or the day in aeon.planner.open (set by a
                       day of Home's week strip), in the Day view
  next / prev          Day view: one day on / back
  right / left         Week view: to the next / previous day that has something on it (changes week when needed)
  focus                from the options back to the list of the selected day
  view                 switch between the Day and the Week view
  weekstart            first day of the week: Monday -> Tuesday ... -> Sunday -> Monday
  what                 what is listed: episodes and films -> episodes -> films
  spotdays / spotwhat  the spotlight of the Planner item on Home: days ahead (7, 14, 1, 3, off) and its content
  refresh              how often the list is read again: daily -> weekly -> every 2 weeks (default) -> monthly
  update               read the list again now (in this script, short pauses), then show the new list
  watching             Fused Glass (0.3.74): Shows you watch on / off - only episodes of shows with a watched episode
  bg                   Fused Glass: the Planner's background, Colors (default) -> Neutral -> Fanart

Window(Home) properties, all starting with aeon.planner.:
  mode (day / week), date (ISO, the selected day), title ('Wednesday 11 Nov 2026'), weektitle ('9 - 15 Nov 2026'),
  col (1-7, column of the selected day), flip (0 / 1, changes on every move: the skin's slide animation hangs on it),
  dir (next / prev), weekstart (name of the first weekday), what (name of the content choice),
  refreshname ('Every 2 weeks'), updated ('12 Nov 2026', 'Updating...'),
  c1 .. c7 . iso / name / num / past / today / sel / count   - the seven days of the week on screen
  Fused Glass (0.3.74): headline ('Next 7 days' when the week starts today, else weektitle), watching (1 / ''),
  watchname (On / Off), bgname (Colors / Neutral / Fanart), summary ('21 episodes, 1 film').
  0.3.78: busy ('1' while the lists are filled: the window opening - the skin sets it in onload - and the commands
  in BUSY_COMMANDS; the skin then says Loading instead of "Nothing planned"), aired (the cached Earlier days list).
  Week starts can also be Today (Skin.String(aeon.planner.weekstart) = today): the week is the next seven days."""
import datetime
import json
import time

import xbmc
import xbmcgui

import nextaired
from resources.lib import planner
from resources.lib.lang import L

# the refresh choice's name (planner.REFRESH_NAMES in English) as a string id
REFRESH_IDS = {'daily': 32017, 'weekly': 32018, '': 32019, 'monthly': 32020}

PROP = 'aeon.planner.'
DAY_LIST = 9500
WEEK_LIST = 9510           # + column (1-7)
WHAT = ('', 'episodes', 'films')
SPOT_DAYS = ('', '14', '1', '3', 'off')        # '' = 7 days


def setting(name):
    return xbmc.getInfoLabel('Skin.String(aeon.planner.%s)' % name)


def week_start():
    value = setting('weekstart')
    if value == 'today':                                # the next seven days (Fused Glass, 0.3.74)
        return datetime.date.today().weekday()
    return int(value) if value in ('1', '2', '3', '4', '5', '6') else 0


WEEKSTARTS = ('', '1', '2', '3', '4', '5', '6', 'today')
BACKGROUNDS = ('', 'neutral', 'fanart')               # '' = Colors


def skin_text(ident, default):
    try:
        import xbmcaddon
        return xbmcaddon.Addon('skin.aeon.fuse').getLocalizedString(ident) or default
    except Exception:
        return default


def watched_titles():
    """Titles of the library shows with at least one watched episode."""
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'VideoLibrary.GetTVShows', 'params': {'properties': ['title', 'watchedepisodes']}})
    shows = (json.loads(xbmc.executeJSONRPC(request)).get('result') or {}).get('tvshows') or []
    return [show.get('title') or '' for show in shows if show.get('watchedepisodes')]


def words():
    weekdays = [xbmc.getLocalizedString(number) for number in range(11, 18)]
    months = [xbmc.getLocalizedString(number) for number in range(21, 33)]
    return weekdays, months


def earlier_on():
    return xbmc.getCondVisibility('Skin.HasSetting(aeon.planner.past)')


def week_first(today):
    """The first day of the week that holds today (Earlier days go back to it, no further)."""
    return planner.week_dates(today, 0, week_start())[0]


AIRED = PROP + 'aired'      # Home property: the cached Earlier days list (JSON: key, time, entries), 0.3.78


def aired(first, today):
    """Library episodes that aired from `first` to yesterday, as Planner entries (Earlier days, 0.3.76). The query
    takes about a second on a large library (67,000 episodes on the box), so the result is kept for ten minutes in
    a Home property, for this week, today and the library's episode count (0.3.78); the day lists read it too."""
    if first >= today:
        return []
    home = xbmcgui.Window(10000)
    key = planner.aired_cache_key(first, today, home.getProperty('aeon.count.episodes'))
    cached = planner.aired_cached(home.getProperty(AIRED), key, time.time())
    if cached is not None:
        return cached
    found = query_aired(first, today)
    home.setProperty(AIRED, json.dumps({'key': key, 'time': time.time(), 'entries': found}))
    return found


def query_aired(first, end):
    """The library's episodes that aired from `first` up to the day before `end`, as Planner entries."""
    days = [(first + datetime.timedelta(days=n)).isoformat() for n in range((end - first).days)]
    rule = {'or': [{'field': 'airdate', 'operator': 'is', 'value': day} for day in days]}
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'VideoLibrary.GetEpisodes',
                          'params': {'filter': rule, 'properties': ['title', 'showtitle', 'season', 'episode', 'firstaired', 'plot', 'art']}})
    return planner.aired_entries((json.loads(xbmc.executeJSONRPC(request)).get('result') or {}).get('episodes') or [])


def aired_on(day, today):
    """The library episodes that aired on one day before today in this week (a day list of Earlier days): from the
    week's cached list when the Planner has made it, else one query for that day (the lists of a week that opens load
    side by side; six week queries at once would only slow each other down)."""
    home = xbmcgui.Window(10000)
    first = week_first(today)
    found = planner.aired_cached(home.getProperty(AIRED), planner.aired_cache_key(first, today, home.getProperty('aeon.count.episodes')),
                                 time.time())
    if found is None:
        found = query_aired(day, day + datetime.timedelta(days=1))
    return [entry for entry in found if entry.get('premiered') == day.isoformat()]


def entries():
    """Episodes and / or films of the kept list, as the 'what' choice says; with Shows you watch on, only the episodes
    of shows with a watched episode. Earlier days on: the days before today hold the library's aired episodes only,
    exactly what their lists show (planner.earlier_mix, 0.3.78)."""
    found = nextaired.kept(setting('what'))
    if earlier_on():
        today = datetime.date.today()
        found = planner.earlier_mix(found, aired(week_first(today), today) if setting('what') != 'films' else [], today)
    if xbmc.getCondVisibility('Skin.HasSetting(aeon.planner.watching)'):
        found = planner.only_watched(found, watched_titles())
    return found


def publish(home, today, current, mode, days, direction):
    weekdays, months = words()
    start = week_start()
    week, column = planner.locate(today, current, start)
    dates = planner.week_dates(today, week, start)
    home.setProperty(PROP + 'mode', mode)
    home.setProperty(PROP + 'date', current.isoformat())
    home.setProperty(PROP + 'title', planner.day_title(current, weekdays, months))
    first, last = dates[0], dates[-1]
    home.setProperty(PROP + 'weektitle', '%d %s - %d %s %d' % (first.day, months[first.month - 1][:3], last.day, months[last.month - 1][:3], last.year))
    home.setProperty(PROP + 'col', str(column + 1))
    home.setProperty(PROP + 'dir', direction)
    home.setProperty(PROP + 'weekstart', xbmc.getLocalizedString(33006) if setting('weekstart') == 'today' else weekdays[start])
    # Fused Glass (0.3.74)
    rolling = setting('weekstart') == 'today' and first == today
    if rolling:
        headline = skin_text(32524, 'Next 7 days')
    elif week in (0, 1):
        headline = skin_text(32539, 'This week') if week == 0 else skin_text(32540, 'Next week')
    else:
        headline = home.getProperty(PROP + 'weektitle')
    home.setProperty(PROP + 'headline', headline)
    # Day view headline (0.3.76): Today / Tomorrow / the weekday, the date under PLANNER
    if current == today:
        dayname = xbmc.getLocalizedString(33006)
    elif current == today + datetime.timedelta(days=1):
        dayname = xbmc.getLocalizedString(33007)
    else:
        dayname = weekdays[current.weekday()]
    home.setProperty(PROP + 'dayname', dayname)
    home.setProperty(PROP + 'daydate', '%d %s %d' % (current.day, months[current.month - 1], current.year))
    # the week slides in only when the week changes, not on every move inside it
    if home.getProperty(PROP + 'wfirst') != first.isoformat():
        home.setProperty(PROP + 'wfirst', first.isoformat())
        home.setProperty(PROP + 'wflip', '' if home.getProperty(PROP + 'wflip') else '1')
    watching = xbmc.getCondVisibility('Skin.HasSetting(aeon.planner.watching)')
    home.setProperty(PROP + 'watching', '1' if watching else '')
    home.setProperty(PROP + 'watchname', skin_text(31547, 'On') if watching else skin_text(31548, 'Off'))
    home.setProperty(PROP + 'pastname', skin_text(31547, 'On') if earlier_on() else skin_text(31548, 'Off'))
    background = setting('bg') if setting('bg') in BACKGROUNDS else ''
    home.setProperty(PROP + 'bgname', {'': skin_text(31551, 'Colors'), 'neutral': skin_text(31549, 'Neutral'),
                                       'fanart': skin_text(31550, 'Fanart')}[background])
    kinds = {}
    for date in dates:
        for entry in days.get(date) or ():
            kind = entry.get('kind') or 'episode'
            kinds[kind] = kinds.get(kind, 0) + 1
    summary = planner.week_summary(kinds, skin_text(32530, '1 episode'), skin_text(32531, '{n} episodes'),
                                   skin_text(32532, '1 film'), skin_text(32533, '{n} films'))
    home.setProperty(PROP + 'summary', skin_text(32529, '{n} this week').replace('{n}', summary) if summary else '')
    home.setProperty(PROP + 'what', {'': xbmc.getLocalizedString(20360) + ' + ' + xbmc.getLocalizedString(20342),
                                     'episodes': xbmc.getLocalizedString(20360), 'films': xbmc.getLocalizedString(20342)}[setting('what') if setting('what') in WHAT else ''])
    for index, date in enumerate(dates, 1):
        base = '%sc%d.' % (PROP, index)
        home.setProperty(base + 'iso', date.isoformat())
        home.setProperty(base + 'name', weekdays[date.weekday()])
        home.setProperty(base + 'num', '%d %s' % (date.day, months[date.month - 1][:3]))
        home.setProperty(base + 'day', str(date.day))                               # Fused Glass (0.3.74)
        home.setProperty(base + 'short', '%s %d' % (weekdays[date.weekday()][:3], date.day))
        home.setProperty(base + 'past', '1' if date < today else '')
        home.setProperty(base + 'today', '1' if date == today else '')
        home.setProperty(base + 'sel', '1' if date == current else '')
        home.setProperty(base + 'count', str(len(days.get(date) or ())))
    names = {'': xbmc.getLocalizedString(20360) + ' + ' + xbmc.getLocalizedString(20342), 'episodes': xbmc.getLocalizedString(20360),
             'films': xbmc.getLocalizedString(20342)}
    spot = setting('spotdays')
    home.setProperty(PROP + 'spotdays', xbmc.getLocalizedString(1223) if spot == 'off' else '%s %s' % (spot or '7', xbmc.getLocalizedString(12393)))
    home.setProperty(PROP + 'spotwhat', names[setting('spotwhat') if setting('spotwhat') in WHAT else ''])
    choice = nextaired.refresh_setting()
    home.setProperty(PROP + 'refreshname', L(REFRESH_IDS[choice]) if choice in REFRESH_IDS else planner.REFRESH_NAMES[choice])
    kept = nextaired.read()
    stamp = float(kept.get('time') or kept.get('tried') or 0)
    if home.getProperty(PROP + 'updating'):
        home.setProperty(PROP + 'updated', L(32016))
    elif stamp:
        when = datetime.date.fromtimestamp(stamp)
        home.setProperty(PROP + 'updated', '%d %s %d' % (when.day, months[when.month - 1][:3], when.year))
    else:
        home.setProperty(PROP + 'updated', '-')
    home.setProperty(PROP + 'flip', '' if home.getProperty(PROP + 'flip') else '1')
    return column + 1


# 0.3.78: a list can only hold the focus while it has items (or is loading them). Setting the focus on an empty list
# drops it altogether, and a focused list that comes back empty hands it to the window's default control (the View
# pill): with Earlier days on that left the Planner stuck in its top row. So a focused list that is about to load other
# items hands the focus to its view's holding button first (9501 Day, 9518 Week: invisible, Left / Right / Up work as
# on the list), and the focus goes to the new list only once it has loaded and has items.
HOLD = {'day': DAY_LIST + 1, 'week': WEEK_LIST + 8}
LISTS = (DAY_LIST,) + tuple(WEEK_LIST + n for n in range(1, 8))
BUSY = PROP + 'busy'       # set while the lists are (re)filled: the skin shows Loading, never "Nothing planned"
BUSY_COMMANDS = ('init', 'view', 'weekstart', 'watching', 'past', 'what', 'update')


def focused():
    try:
        return int(xbmc.getInfoLabel('System.CurrentControlId') or 0)
    except ValueError:
        return 0


def settle(target, reload):
    """Wait until list `target` has its items: when its content changes (reload), first until Kodi starts loading it
    (at most 0.6 s), then until it is done (at most 8 s). Returns the number of items."""
    updating = 'Container(%d).IsUpdating' % target
    if reload:
        for _ in range(12):
            if xbmc.getCondVisibility(updating):
                break
            xbmc.sleep(50)
    for _ in range(80):
        if not xbmc.getCondVisibility(updating):
            break
        xbmc.sleep(100)
    try:
        return int(xbmc.getInfoLabel('Container(%d).NumItems' % target) or 0)
    except ValueError:
        return 0


def focus(mode, column, reload, allowed):
    """The focus to the list of the selected day once it has loaded; to the view's holding button when the list is
    empty. Left alone when the user has moved somewhere else meanwhile (allowed: where it may be taken from)."""
    target = DAY_LIST if mode == 'day' else WEEK_LIST + column
    count = settle(target, reload)
    if focused() in allowed:
        xbmc.executebuiltin('SetFocus(%d)' % (target if count else HOLD[mode]))


def main(command):
    home = xbmcgui.Window(10000)
    # the run that sets busy clears it (an Update now pressed again while one runs leaves it to the first)
    owner = command in BUSY_COMMANDS and not (command == 'update' and home.getProperty(PROP + 'updating'))
    if owner:
        home.setProperty(BUSY, '1')
    try:
        run(home, command)
    finally:
        if owner:
            home.clearProperty(BUSY)


def run(home, command):
    start = focused()
    allowed = set(LISTS) | set(HOLD.values()) | {start, 0}
    today = datetime.date.today()
    earliest = week_first(today) if earlier_on() else today
    days = planner.group(entries(), earliest)
    old = (home.getProperty(PROP + 'mode'), home.getProperty(PROP + 'date'), home.getProperty(PROP + 'wfirst'))
    mode = home.getProperty(PROP + 'mode') or setting('view') or 'day'
    if mode not in ('day', 'week'):
        mode = 'day'
    current = planner.parse(home.getProperty(PROP + 'date')) or today
    if current < earliest:
        current = today
    direction = 'next'
    refocus = False

    if command == 'init':
        mode = setting('view') if setting('view') in ('day', 'week') else 'day'
        current = today if mode == 'day' else planner.first_planned(today, days)
        # 0.3.59: opened from a day of Home's week strip: that day, in the Day view (the saved view stays as it was)
        wanted = planner.parse(home.getProperty(PROP + 'open'))
        home.clearProperty(PROP + 'open')
        if wanted is not None and wanted >= today:
            mode, current = 'day', wanted
        refocus = True
    elif command in ('next', 'prev'):
        current = planner.step_day(today, current, 1 if command == 'next' else -1, days, earliest)
        direction = command
        refocus = True
    elif command in ('right', 'left'):
        current = planner.step_column(today, current, 1 if command == 'right' else -1, days, earliest)
        direction = 'next' if command == 'right' else 'prev'
        refocus = True
    elif command == 'focus':
        if mode == 'week' and current not in days:
            current = planner.first_planned(today, days)
        refocus = True
    elif command == 'view':
        mode = 'week' if mode == 'day' else 'day'
        xbmc.executebuiltin('Skin.SetString(aeon.planner.view,%s)' % mode)
        if mode == 'week' and current not in days:
            current = planner.first_planned(today, days)
        refocus = True
    elif command == 'weekstart':
        now = setting('weekstart') if setting('weekstart') in WEEKSTARTS else ''
        nxt = WEEKSTARTS[(WEEKSTARTS.index(now) + 1) % len(WEEKSTARTS)]
        xbmc.executebuiltin('Skin.SetString(aeon.planner.weekstart,%s)' % nxt if nxt else 'Skin.Reset(aeon.planner.weekstart)')
        xbmc.sleep(150)
    elif command == 'watching':
        xbmc.executebuiltin('Skin.ToggleSetting(aeon.planner.watching)')
        xbmc.sleep(150)
        days = planner.group(entries(), earliest)
        if mode == 'week' and current not in days:
            current = planner.first_planned(today, days)
    elif command == 'past':
        xbmc.executebuiltin('Skin.ToggleSetting(aeon.planner.past)')
        xbmc.sleep(150)
        earliest = week_first(today) if earlier_on() else today
        days = planner.group(entries(), earliest)
        if current < earliest:
            current = today
    elif command == 'bg':
        now = setting('bg') if setting('bg') in BACKGROUNDS else ''
        nxt = BACKGROUNDS[(BACKGROUNDS.index(now) + 1) % len(BACKGROUNDS)]
        xbmc.executebuiltin('Skin.SetString(aeon.planner.bg,%s)' % nxt if nxt else 'Skin.Reset(aeon.planner.bg)')
        xbmc.sleep(150)
    elif command in ('spotdays', 'spotwhat'):
        choices = SPOT_DAYS if command == 'spotdays' else WHAT
        now = setting(command) if setting(command) in choices else ''
        nxt = choices[(choices.index(now) + 1) % len(choices)]
        xbmc.executebuiltin('Skin.SetString(aeon.planner.%s,%s)' % (command, nxt) if nxt else 'Skin.Reset(aeon.planner.%s)' % command)
        xbmc.sleep(150)
    elif command == 'refresh':
        nxt = planner.next_refresh(nextaired.refresh_setting())
        xbmc.executebuiltin('Skin.SetString(aeon.planner.refresh,%s)' % nxt if nxt else 'Skin.Reset(aeon.planner.refresh)')
        xbmc.sleep(150)
    elif command == 'update':
        if home.getProperty(PROP + 'updating'):
            return
        home.setProperty(PROP + 'updating', '1')
        publish(home, today, current, mode, days, direction)
        try:
            nextaired.build(xbmc.Monitor(), step=0.1)       # Update now: shorter pauses, the user waits
        finally:
            home.clearProperty(PROP + 'updating')
        days = planner.group(entries(), earliest)
        refocus = True
        xbmc.executebuiltin('Container.Refresh')
    elif command == 'what':
        now = setting('what') if setting('what') in WHAT else ''
        nxt = WHAT[(WHAT.index(now) + 1) % len(WHAT)]
        xbmc.executebuiltin('Skin.SetString(aeon.planner.what,%s)' % nxt if nxt else 'Skin.Reset(aeon.planner.what)')
        xbmc.sleep(150)
        days = planner.group(entries(), earliest)
        if mode == 'week' and current not in days:
            current = planner.first_planned(today, days)
    # does the list of the selected day get other items? (a new day in the Day view, a new week in the Week view, a
    # new view, or the window just opened) Then a list that has the focus hands it to the holding button first.
    first = planner.week_dates(today, planner.locate(today, current, week_start())[0], week_start())[0]
    reload = (command in BUSY_COMMANDS or old[0] != mode or
              (old[1] != current.isoformat() if mode == 'day' else old[2] != first.isoformat()))
    if refocus and reload and focused() in LISTS:
        xbmc.executebuiltin('SetFocus(%d)' % HOLD[mode])
    column = publish(home, today, current, mode, days, direction)
    if refocus and (mode == 'day' or current in days):
        focus(mode, column, reload, allowed)
    elif command in BUSY_COMMANDS:
        settle(DAY_LIST if mode == 'day' else WEEK_LIST + column, True)    # Loading until the list has its items
