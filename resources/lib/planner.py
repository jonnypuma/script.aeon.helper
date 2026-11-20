# -*- coding: utf-8 -*-
"""Calendar logic of the Planner (upcoming episodes and films). No Kodi imports.

The Planner never shows a day before today (Earlier days on: before the first day of this week). A week runs from the chosen first weekday (0 = Monday .. 6 = Sunday);
week 0 is the week that contains today."""
import datetime
import re


def parse(text):
    try:
        return datetime.datetime.strptime((text or '')[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def week_dates(today, week, week_start=0):
    """The seven dates of week number `week` (0 = this week)."""
    first = today - datetime.timedelta(days=(today.weekday() - week_start) % 7) + datetime.timedelta(weeks=week)
    return [first + datetime.timedelta(days=offset) for offset in range(7)]


def locate(today, date, week_start=0):
    """(week, column 0..6) of a date."""
    first = week_dates(today, 0, week_start)[0]
    days = (date - first).days
    return days // 7, days % 7


def day_title(date, weekdays, months):
    """'Wednesday 11 Nov 2026' - weekdays: Monday first, months: January first (full names; the month is cut to three letters)."""
    return '%s %d %s %d' % (weekdays[date.weekday()], date.day, months[date.month - 1][:3], date.year)


def group(entries, today):
    """{date: [entries]} for today and later, each day sorted by time (when known) then name."""
    days = {}
    for entry in entries or ():
        date = parse(entry.get('premiered'))
        if date is None or date < today:
            continue
        days.setdefault(date, []).append(entry)
    for date in days:
        days[date].sort(key=lambda entry: (entry.get('time') or '99:99', (entry.get('showtitle') or entry.get('title') or '').lower(),
                                           entry.get('season') or 0, entry.get('episode') or 0))
    return days


def last_day(days, today):
    """The last date the Planner can show: the last one with something on it (today when there is nothing)."""
    return max(days) if days else today


def step_day(today, current, step, days, earliest=None):
    """Day view: the next / previous day, never before today (or `earliest`: Earlier days on, 0.3.76), never past the
    last planned day."""
    first = earliest or today
    target = current + datetime.timedelta(days=step)
    if target < first:
        return first
    if target > last_day(days, today):
        return current
    return target


def step_column(today, current, step, days, earliest=None):
    """Week view: the next / previous day that has something on it (so the focus always lands on a list).
    Returns the same day when there is none in that direction. earliest: the first day allowed (default today)."""
    planned = sorted(date for date in days if date >= (earliest or today))
    if step > 0:
        later = [date for date in planned if date > current]
        return later[0] if later else current
    earlier = [date for date in planned if date < current]
    return earlier[-1] if earlier else current


def first_planned(today, days):
    planned = sorted(date for date in days if date >= today)
    return planned[0] if planned else today


def day_label(date, today, words):
    """'Today', 'Tomorrow' or the weekday name. words: {'today', 'tomorrow', 'weekdays': [Monday .. Sunday]}."""
    delta = (date - today).days
    if delta == 0:
        return words['today']
    if delta == 1:
        return words['tomorrow']
    return words['weekdays'][date.weekday()]


def headings(dates, today, words, months):
    """For a list of ISO dates in order: [(day label, 'D Month') on the first row of each day, ('', '') on the others]."""
    out = []
    last = None
    for text in dates:
        if text == last:
            out.append(('', ''))
            continue
        last = text
        date = parse(text)
        if date is None:
            out.append(('', text or ''))
            continue
        out.append((day_label(date, today, words), '%d %s' % (date.day, months[date.month - 1])))
    return out


def cast_list(raw, limit=12):
    """The first actors of a JSON-RPC cast list as [{'name', 'role', 'thumbnail'}], names only once."""
    found = []
    seen = set()
    for actor in raw or ():
        name = (actor.get('name') or '').strip() if isinstance(actor, dict) else ''
        if not name or name in seen:
            continue
        seen.add(name)
        found.append({'name': name, 'role': actor.get('role') or '', 'thumbnail': actor.get('thumbnail') or ''})
        if len(found) >= limit:
            break
    return found


def details(entry, custom=None):
    """What is kept of a TMDb Helper list entry besides the basics: genre, certificate, studio, rating, cast, network."""
    custom = custom or {}
    try:
        rating = round(float(entry.get('rating') or 0), 1)
    except (TypeError, ValueError):
        rating = 0.0
    try:
        votes = int(entry.get('votes') or 0)
    except (TypeError, ValueError):
        votes = 0
    return {'genre': [text for text in entry.get('genre') or () if text], 'mpaa': entry.get('mpaa') or '',
            'studio': [text for text in entry.get('studio') or () if text], 'rating': rating, 'votes': votes,
            'cast': cast_list(entry.get('cast')), 'network': custom.get('network') or ''}


# ------------------------------------------------------------------ next episodes, one show at a time
# TMDb Helper's "library: airing next" list asks TMDb about every show of the library (2,142 on the box) in up to 40
# threads at once; on a 4 GB box that ran into TMDb's rate limit and ground Kodi to a halt for many minutes. Only the
# shows that can still get episodes are asked now, one at a time, through TMDb Helper's details of the show
# (its next_aired.* properties).
ENDED = ('ended', 'canceled', 'cancelled', 'deleted')
QUIET = 180                   # seconds after playback (playing or paused) and without a key press before a read starts


def quiet_enough(now, last_played, idle_ok, quiet=QUIET):
    """May the Planner list be read now? Never during playback (the caller checks that first and keeps last_played
    current while something plays), and only once playback has been over for `quiet` seconds and nobody has pressed
    a key for as long (idle_ok: System.IdleTime(quiet)). Kodi's idle time keeps counting during a film, so the end of
    playback is timed by the caller."""
    return bool(idle_ok) and now - last_played >= quiet
SHOW_ART = ('poster', 'fanart', 'clearlogo', 'landscape')


def airing_candidates(shows):
    """The library shows that can still get new episodes and have a TMDb id: (title, tmdb id) pairs."""
    out = []
    for show in shows or ():
        tmdb = str((show.get('uniqueid') or {}).get('tmdb') or '').strip()
        if not tmdb or (show.get('status') or '').strip().lower() in ENDED:
            continue
        out.append((show.get('title') or show.get('label') or '', tmdb))
    return out


def next_episode(showtitle, entry, custom, today):
    """The next episode from TMDb Helper's details of a show (next_aired.* properties), in the kept list's shape;
    None when the show has no next episode, or its date has passed."""
    custom = custom or {}
    date = (custom.get('next_aired.original') or custom.get('next_aired.premiered') or '')[:10]
    if not parse(date) or date < today.isoformat():
        return None
    try:
        season = int(custom.get('next_aired.season') or 0)
        episode = int(custom.get('next_aired.episode') or 0)
    except (TypeError, ValueError):
        return None
    try:
        runtime = int(float(custom.get('next_aired.duration') or 0))
    except (TypeError, ValueError):
        runtime = 0
    shown = entry.get('art') or {}
    art = {}
    for name in SHOW_ART:
        if shown.get(name):
            art[name] = shown[name]
            art['tvshow.' + name] = shown[name]
    still = custom.get('next_aired.thumb') or shown.get('landscape') or shown.get('fanart')
    if still:
        art['thumb'] = still
    return {'showtitle': showtitle or entry.get('title') or '', 'title': custom.get('next_aired.title') or '',
            'season': season, 'episode': episode, 'premiered': date, 'plot': custom.get('next_aired.plot') or '',
            'runtime': runtime, 'art': art}


# ------------------------------------------------------------------ premieres and finales (0.3.97)
# The user (2026-11-17): "show if next airing episode is a series finale, a season finale, a series premiere, a season
# premiere ... in the planner as well". TMDb marks an episode's type; TMDb Helper's details of an episode carry it as
# episode_type (series_premiere, season_premiere, mid_season_finale, season_finale, standard, special).
EPKIND_WORDS = {'series_premiere': 32048, 'season_premiere': 32049, 'mid_season_finale': 32050, 'season_finale': 32051,
                'series_finale': 32052}
ENDED = ('ended', 'canceled', 'cancelled')


def episode_kind(season, episode, episode_type='', show_status=''):
    """series_premiere / season_premiere / mid_season_finale / season_finale / series_finale, or '' (a standard episode
    or a special). The first episode of a season is a premiere whatever TMDb says; a finale of a show that has ended is
    the series finale."""
    try:
        season, episode = int(season or 0), int(episode or 0)
    except (TypeError, ValueError):
        return ''
    if season < 1 or episode < 1:
        return ''
    if episode == 1:
        return 'series_premiere' if season == 1 else 'season_premiere'
    kind = (episode_type or '').strip().lower().replace('-', '_').replace(' ', '_')
    if kind in ('series_finale',):
        return 'series_finale'
    if kind in ('finale', 'season_finale'):
        return 'series_finale' if (show_status or '').strip().lower() in ENDED else 'season_finale'
    if kind in ('mid_season', 'mid_season_finale'):
        return 'mid_season_finale'
    return ''


def entry_kind(entry):
    """The kind of a kept Planner entry: what the list build stored (0.3.97+), else, for a list kept from before
    (no 'epkind' key), the premieres the season and episode numbers give. Films and albums have none."""
    kind = entry.get('epkind')
    if kind is None and (entry.get('kind') or 'episode') == 'episode':
        kind = episode_kind(entry.get('season'), entry.get('episode'))
    return kind or ''


# ------------------------------------------------------------------ the kept Next Aired list
# Skin.String(aeon.planner.refresh): how often the list is read again. '' = every two weeks (the default).
REFRESH = ('daily', 'weekly', '', 'monthly')
REFRESH_DAYS = {'daily': 1, 'weekly': 7, '': 14, 'monthly': 30}
REFRESH_NAMES = {'daily': 'Daily', 'weekly': 'Weekly', '': 'Every 2 weeks', 'monthly': 'Monthly'}
RETRY = 6 * 3600              # a read that came back (partly) empty is tried again after six hours


def refresh_choice(value):
    return value if value in REFRESH else ''


def next_refresh(value):
    """The interval after this one, as the Planner option cycles: daily -> weekly -> every 2 weeks -> monthly."""
    return REFRESH[(REFRESH.index(refresh_choice(value)) + 1) % len(REFRESH)]


def retry_after(data):
    """Seconds to wait after a read that came back (partly) empty: 6 h, then 12 h, 24 h, 48 h, at most 4 days. TMDb
    Helper's list can fail on a whole library (and keep the box busy while it does), so it is not asked again soon."""
    failures = max(1, int(data.get('failures') or 1))
    return RETRY * 2 ** min(failures - 1, 4)


def due(data, choice, now):
    """Is the kept list to be read again? A list that was only partly read (a source came back empty) is tried again
    after retry_after(); a complete one after the chosen interval; nothing kept at all: now."""
    kept = float(data.get('time') or 0)
    if data.get('partial') or (kept and not data.get('episodes')):
        # partly read, or kept without a single episode (a read before 0.25.0 could wipe them): try again later
        return now - max(kept, float(data.get('tried') or 0)) > retry_after(data)
    if not kept:
        return now - float(data.get('tried') or 0) > retry_after(data) if data.get('tried') else True
    return now - kept > REFRESH_DAYS[refresh_choice(choice)] * 86400


def merge(old, episodes, movies, now):
    """The list to keep after a read. A part that came back empty (TMDb Helper busy, no network) never wipes what was
    kept: the old part stays and the list is marked partial, so it is tried again soon."""
    old = old or {}
    data = {'time': now, 'tried': now, 'episodes': episodes or [], 'movies': movies or []}
    partial = False
    if not episodes:
        data['episodes'] = old.get('episodes') or []
        partial = True
    if not movies:
        data['movies'] = old.get('movies') or []
        partial = True
    if partial:
        data['partial'] = True
        data['time'] = float(old.get('time') or 0)
        data['failures'] = int(old.get('failures') or 0) + 1 if not episodes else 0
    return data


def week_counts(entries, today, n=7):
    """[(date, count)] for today and the n - 1 days after it: how many episodes and films come out each day."""
    counts = {}
    for entry in entries or ():
        date = parse(entry.get('premiered'))
        if date is not None:
            counts[date] = counts.get(date, 0) + 1
    return [(today + datetime.timedelta(days=i), counts.get(today + datetime.timedelta(days=i), 0)) for i in range(n)]


def week_kinds(entries, today, n=7):
    """[(date, episodes, films, albums)] for today and the n - 1 days after it (Home > Planner week strip, 0.39.2)."""
    counts = {}
    for entry in entries or ():
        date = parse(entry.get('premiered'))
        if date is None:
            continue
        kind = entry.get('kind') or 'episode'
        slot = counts.setdefault(date, [0, 0, 0])
        slot[1 if kind == 'movie' else 2 if kind == 'album' else 0] += 1
    out = []
    for i in range(n):
        date = today + datetime.timedelta(days=i)
        eps, films, albums = counts.get(date, (0, 0, 0))
        out.append((date, eps, films, albums))
    return out


# 0.3.69 placeholder texts from release calendars ("None" showed as the plot of an episode on the Planner spotlight)
PLACEHOLDERS = ('none', 'null', 'n/a', 'na', 'tba', 'tbd', '-', '...')
GENERIC_TITLE = re.compile(r'^(episode|ep\.?|aflevering|folge|épisode|episodio|episódio|avsnitt|jakso|odcinek|epizoda|'
                           r'epizód|bölüm|эпизод|серия)?\s*#?\s*\d+$', re.IGNORECASE)


def text_or_empty(value):
    """The text, or '' for a missing value or a placeholder ("None", "TBA", "N/A" ...)."""
    if value is None:
        return ''
    text = value.strip() if isinstance(value, str) else str(value).strip()
    return '' if text.lower() in PLACEHOLDERS else text


def real_episode_title(title):
    """The episode's title when it says something; '' for "Episode 2", "Folge 2", "#2", "TBA": the spotlights spell
    out Season / Episode themselves, so a generic title would only repeat it."""
    text = text_or_empty(title)
    return '' if GENERIC_TITLE.match(text) else text


def only_watched(entries, titles):
    """Fused Glass Planner > Shows you watch (0.3.74): the episodes of the shows in `titles` (shows with a watched
    episode in the library), films and albums untouched."""
    keep = set((title or '').strip().lower() for title in titles)
    return [entry for entry in entries or ()
            if (entry.get('kind') or 'episode') != 'episode' or (entry.get('showtitle') or '').strip().lower() in keep]


def behind(on, entry):
    """True when the episode to continue, (season, episode), comes before this airing episode: the Planner then says
    "You're on S3 E1" on it."""
    if not on or (entry.get('kind') or 'episode') != 'episode':
        return False
    return (int(on[0] or 0), int(on[1] or 0)) < (int(entry.get('season') or 0), int(entry.get('episode') or 0))


def week_summary(kinds, one_ep, many_ep, one_film, many_film):
    """{'episode': 21, 'movie': 1} -> '21 episodes, 1 film' with the given patterns ({n}); '' when nothing is on."""
    parts = []
    for count, one, many in ((kinds.get('episode', 0), one_ep, many_ep), (kinds.get('movie', 0), one_film, many_film)):
        if count:
            parts.append(one if count == 1 else many.replace('{n}', str(count)))
    return ', '.join(parts)


def aired_entries(episodes):
    """Library episodes (JSON-RPC: title, showtitle, season, episode, firstaired, plot, art) -> Planner entries for the
    days before today (Earlier days, 0.3.76)."""
    out = []
    for ep in episodes or ():
        if not ep.get('firstaired'):
            continue
        out.append({'kind': 'episode', 'showtitle': ep.get('showtitle') or '', 'title': ep.get('title') or '',
                    'season': ep.get('season') or 0, 'episode': ep.get('episode') or 0, 'premiered': ep['firstaired'][:10],
                    'plot': ep.get('plot') or '', 'art': dict(ep.get('art') or {}), 'more': {}, 'aired': True})
    return out


def earlier_mix(kept, aired, today):
    """Earlier days on (0.3.78): the kept list from today on, plus the library's episodes that aired before today.
    The kept list still holds what was to come when it was read, but the lists of the days before today show only the
    library's episodes, so its older entries are left out: the Planner never counts or steps onto a day for titles
    its list does not show (that left the focus on an empty list). Entries without a date stay with the kept part
    (group() drops them)."""
    out = [entry for entry in kept or () if (parse(entry.get('premiered')) or today) >= today]
    for entry in aired or ():
        date = parse(entry.get('premiered'))
        if date is not None and date < today:
            out.append(entry)
    return out


def aired_cache_key(first, today, episodes):
    """The key the cached Earlier days list is kept under (0.3.78): the week's first day, today, and the library's
    episode count (aeon.count.episodes, new after every scan or clean)."""
    return '%s|%s|%s' % (first.isoformat(), today.isoformat(), episodes or '')


def aired_cached(raw, key, now, ttl=600):
    """The entries of a cached Earlier days list (JSON text) when it is for this key and younger than ttl seconds,
    else None."""
    import json
    try:
        data = json.loads(raw or '{}')
    except ValueError:
        return None
    if not isinstance(data, dict) or data.get('key') != key or not isinstance(data.get('entries'), list):
        return None
    try:
        age = now - float(data.get('time') or 0)
    except (TypeError, ValueError):
        return None
    return data['entries'] if 0 <= age < ttl else None
