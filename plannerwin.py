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

Window(Home) properties, all starting with aeon.planner.:
  mode (day / week), date (ISO, the selected day), title ('Wednesday 11 Nov 2026'), weektitle ('9 - 15 Nov 2026'),
  col (1-7, column of the selected day), flip (0 / 1, changes on every move: the skin's slide animation hangs on it),
  dir (next / prev), weekstart (name of the first weekday), what (name of the content choice),
  refreshname ('Every 2 weeks'), updated ('12 Nov 2026', 'Updating...'),
  c1 .. c7 . iso / name / num / past / today / sel / count   - the seven days of the week on screen"""
import datetime

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
    return int(value) if value in ('1', '2', '3', '4', '5', '6') else 0


def words():
    weekdays = [xbmc.getLocalizedString(number) for number in range(11, 18)]
    months = [xbmc.getLocalizedString(number) for number in range(21, 33)]
    return weekdays, months


def entries():
    """Episodes and / or films of the kept list, as the 'what' choice says."""
    return nextaired.kept(setting('what'))


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
    home.setProperty(PROP + 'weekstart', weekdays[start])
    home.setProperty(PROP + 'what', {'': xbmc.getLocalizedString(20360) + ' + ' + xbmc.getLocalizedString(20342),
                                     'episodes': xbmc.getLocalizedString(20360), 'films': xbmc.getLocalizedString(20342)}[setting('what') if setting('what') in WHAT else ''])
    for index, date in enumerate(dates, 1):
        base = '%sc%d.' % (PROP, index)
        home.setProperty(base + 'iso', date.isoformat())
        home.setProperty(base + 'name', weekdays[date.weekday()])
        home.setProperty(base + 'num', '%d %s' % (date.day, months[date.month - 1][:3]))
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


def focus(mode, column):
    """Put the focus on the list of the selected day; on an empty day the Day view has a stand-in button (9501)."""
    xbmc.sleep(350)                                   # the lists of a new day or week need a moment
    targets = (DAY_LIST, DAY_LIST + 1) if mode == 'day' else (WEEK_LIST + column,)
    for _ in range(8):
        for target in targets:
            xbmc.executebuiltin('SetFocus(%d)' % target)
            xbmc.sleep(120)
            if xbmc.getCondVisibility('Control.HasFocus(%d)' % target):
                return


def main(command):
    home = xbmcgui.Window(10000)
    today = datetime.date.today()
    days = planner.group(entries(), today)
    mode = home.getProperty(PROP + 'mode') or setting('view') or 'day'
    if mode not in ('day', 'week'):
        mode = 'day'
    current = planner.parse(home.getProperty(PROP + 'date')) or today
    if current < today:
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
        current = planner.step_day(today, current, 1 if command == 'next' else -1, days)
        direction = command
        refocus = True
    elif command in ('right', 'left'):
        current = planner.step_column(today, current, 1 if command == 'right' else -1, days)
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
        nxt = (week_start() + 1) % 7
        xbmc.executebuiltin('Skin.SetString(aeon.planner.weekstart,%d)' % nxt if nxt else 'Skin.Reset(aeon.planner.weekstart)')
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
        days = planner.group(entries(), today)
        refocus = True
        xbmc.executebuiltin('Container.Refresh')
    elif command == 'what':
        now = setting('what') if setting('what') in WHAT else ''
        nxt = WHAT[(WHAT.index(now) + 1) % len(WHAT)]
        xbmc.executebuiltin('Skin.SetString(aeon.planner.what,%s)' % nxt if nxt else 'Skin.Reset(aeon.planner.what)')
        xbmc.sleep(150)
        days = planner.group(entries(), today)
        if mode == 'week' and current not in days:
            current = planner.first_planned(today, days)
    column = publish(home, today, current, mode, days, direction)
    if refocus and (mode == 'day' or current in days):
        focus(mode, column)
