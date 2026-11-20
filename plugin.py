# -*- coding: utf-8 -*-
"""Lists for the Aeon Fuse skin.

plugin://script.aeon.helper/?info=online&list=<name>&type=movie|tv[&year=<y>&query=<title>]
    a TMDb Helper list (trending_week, popular, top_rated, now_playing, upcoming, on_the_air, airing_today,
    recommendations, similar) matched against the library: a title you have comes back as your own library item
    (property aeon.owned = 1; it plays or opens like anywhere else), the others carry aeon.missing = 1 and cannot be
    played - the skin shows them dimmed. query goes last because a title may contain an ampersand.

plugin://script.aeon.helper/?info=favourites&kind=all|video|music|addons
    Kodi's favourites of one group, for Home > Favourites (skin 0.32.0): a favourite that points at a library show, film,
    set, album or artist carries that item's artwork and plot; property aeon.favwhat names what it is. OK runs
    ?info=runfav&n=<index>, which opens it as Kodi's Favourites window does.

plugin://script.aeon.helper/?info=nextaired
    upcoming episodes of the shows in the library (from TMDb Helper, read in the background), soonest first. Opened in
    the Videos window it switches to the Planner view. Nothing in it can be played: it is a calendar.

plugin://script.aeon.helper/?info=picfolders
    the picture sources' folders that hold photos or videos, newest first (resources/lib/picfolders.py walks them; kept
    15 minutes in picfolders.json), for Home > Pictures (skin 0.56.21). Sets the Home window's aeon.pic.* properties
    for the "Newest folder" spotlight; the last card opens the Pictures window. OK on a card runs ?info=picopen.

plugin://script.aeon.helper/?info=ssround&n=<items>&kinds=<movies,tvshows,music,cinema,today,tomorrow>&r=<round>
    one round of the Aeon Fuse screensaver (screensaver.aeon.fuse 1.3.0): n items drawn at random from the sources
    asked for, mixed (resources/lib/ssround.py), each with property aeon.ss.kind; sets Window(Home) aeon.ss.pages (how
    many) and aeon.ss.ready = r when it is done.

plugin://script.aeon.helper/?info=episodes&tvshowid=<id>&season=<n|-1>
    a season's episodes with those that share one video file joined into one row (resources/lib/multiep.py): the
    numbers as a range (property aeon.ep.range, the user's episode code in aeon.ep.code), the title and plot once, the
    file's own running time. The rows are the library's episodes (DBID of the first part, the file as the path), so
    they play, resume and count as watched as usual. The service opens it in place of a season that has such files while
    Skin settings > Details > Episodes in one file as one row is on (skin 0.56.23).

plugin://script.aeon.helper/?info=recentsets[&limit=<n>]
    the movie sets whose films you played last, newest first (default 20): library set folders
    (videodb://movies/sets/<id>/, DBType set, the set's art, lastplayed = its film played last), for Home > Sets.

Artist information page:

plugin://script.aeon.helper/?info=toptracks&artistid=<id>   the artist's most popular tracks
plugin://script.aeon.helper/?info=similar&artistid=<id>     artists like this one

Source: Deezer's public API (the artist's name is sent to api.deezer.com; answers are kept for 30 days in the add-on's
data folder). Tracks and artists that are in the library come first-class: a track plays, an artist opens. The others
carry the property aeon.missing = 1 and the skin shows them dimmed.
With Deezer switched off (Skin.HasSetting(aeon.artist.offline)), unreachable or not knowing the artist, the lists come
from the library alone: the artist's most played songs, and library artists that share its rarer genres."""
import datetime
import json
import os
import sys
import time

try:
    from urllib.parse import parse_qsl, quote, unquote
    from urllib.request import Request, urlopen
except ImportError:                      # pragma: no cover
    from urlparse import parse_qsl
    from urllib import quote, unquote
    from urllib2 import Request, urlopen

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

import artistcache
import menufile
import nextaired
import videocache
from resources.lib import channels, deezer, favourites, favspot, inlibrary, planner, similar
from resources.lib import online as matching

KEEP = 30 * 24 * 3600
NOOP = 'plugin://script.aeon.helper/?info=noop'


def rpc(method, params):
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return json.loads(xbmc.executeJSONRPC(request)).get('result') or {}


def fetch(url):
    request = Request(url, headers={'User-Agent': 'Kodi'})
    return json.loads(urlopen(request, timeout=8).read().decode('utf-8'))


def cache_file(artistid):
    folder = xbmcvfs.translatePath('special://profile/addon_data/script.aeon.helper/deezer/')
    if not xbmcvfs.exists(folder):
        xbmcvfs.mkdirs(folder)
    return os.path.join(folder, '%d.json' % artistid)


def online(artistid, name):
    """Deezer's answer for this artist: from the cache, else fetched. None = use the library."""
    if xbmc.getCondVisibility('Skin.HasSetting(aeon.artist.offline)') or not name:
        return None
    path = cache_file(artistid)
    try:
        with open(path, 'r') as handle:
            data = json.load(handle)
        if time.time() - float(data.get('time') or 0) < KEEP and data.get('name') == name:
            return data.get('found')
    except (IOError, OSError, ValueError):
        pass
    try:
        found = deezer.lookup(fetch, name)
    except Exception as error:           # network, bad JSON, rate limit: fall back to the library, try again next time
        xbmc.log('[script.aeon.helper] Deezer look-up failed: %s' % error, xbmc.LOGINFO)
        return None
    try:
        with open(path, 'w') as handle:
            json.dump({'time': time.time(), 'name': name, 'found': found}, handle)
    except (IOError, OSError):
        pass
    return found


def artist_name(artistid):
    return (rpc('AudioLibrary.GetArtistDetails', {'artistid': artistid}).get('artistdetails') or {}).get('label') or ''


SONG_PROPERTIES = ['title', 'file', 'album', 'thumbnail', 'duration', 'playcount', 'artist', 'track']


def library_songs(artistid, name):
    """The artist's songs, most played first. Asked by name: Kodi answers that in a fraction of the time the id takes."""
    songs = []
    if name:
        songs = rpc('AudioLibrary.GetSongs', {'filter': {'field': 'artist', 'operator': 'is', 'value': name}, 'properties': SONG_PROPERTIES}).get('songs') or []
    if not songs:
        songs = rpc('AudioLibrary.GetSongs', {'filter': {'artistid': artistid}, 'properties': SONG_PROPERTIES}).get('songs') or []
    return sorted(songs, key=lambda song: -(song.get('playcount') or 0))


def library_artists(names):
    """Library artists with exactly these names, album artist or not (someone you only have on a compilation counts)."""
    if not names:
        return []
    reply = rpc('AudioLibrary.GetArtists', {'albumartistsonly': False, 'properties': ['thumbnail'],
                                            'filter': {'field': 'artist', 'operator': 'is', 'value': list(names)}})
    return reply.get('artists') or []


def song_item(song):
    item = xbmcgui.ListItem(label=song.get('title') or song.get('label') or '', offscreen=True)
    tag = item.getMusicInfoTag()
    tag.setMediaType('song')
    tag.setTitle(song.get('title') or '')
    tag.setAlbum(song.get('album') or '')
    tag.setArtist(' / '.join(song.get('artist') or ()))
    tag.setDuration(int(song.get('duration') or 0))
    tag.setDbId(int(song['songid']), 'song')
    if song.get('thumbnail'):
        item.setArt({'thumb': song['thumbnail'], 'icon': song['thumbnail']})
    return song['file'], item, False


def missing_item(label, label2, picture):
    item = xbmcgui.ListItem(label=label, label2=label2, offscreen=True)
    item.setProperty('aeon.missing', '1')
    if label2:
        item.getMusicInfoTag().setAlbum(label2)
    if picture:
        item.setArt({'thumb': picture, 'icon': picture})
    return NOOP, item, False


def top_tracks(artistid):
    name = artist_name(artistid)
    songs = library_songs(artistid, name)
    found = online(artistid, name)
    if not found or not found.get('tracks'):
        return [song_item(song) for song in songs[:12]]
    return [song_item(song) if song else missing_item(track['title'], track['album'], track['cover'])
            for track, song in deezer.match_tracks(found['tracks'], songs)]


def artist_item(artist, picture):
    item = xbmcgui.ListItem(label=artist.get('label') or '', offscreen=True)
    tag = item.getMusicInfoTag()
    tag.setMediaType('artist')
    tag.setArtist(artist.get('label') or '')
    tag.setDbId(int(artist['artistid']), 'artist')
    thumb = artist.get('thumbnail') or picture
    if thumb:
        item.setArt({'thumb': thumb, 'icon': thumb})
    return 'musicdb://artists/%d/' % artist['artistid'], item, True


def similar_artists(artistid):
    found = online(artistid, artist_name(artistid))
    if found and found.get('related'):
        # exact names first (any artist of the library), then the album artists under a normalised name ("The X" = "X")
        known = library_artists([entry['name'] for entry in found['related']]) + (artistcache.load() or [])
        return [artist_item(artist, entry['picture']) if artist else missing_item(entry['name'], '', entry['picture'])
                for entry, artist in deezer.match_artists(found['related'], known)]
    library = artistcache.load()
    if library is None:
        library = artistcache.build() or []
    if not any(artist['artistid'] == artistid for artist in library):
        extra = artistcache.one(artistid)
        if extra:
            library = library + [extra]
    names = set(similar.rank(library, artistid))
    return [artist_item(artist, '') for artist in library if artist['label'] in names]


def artist_albums(artistid, skip=0):
    """0.3.116: the artist's other albums, oldest first (Music information, More by the artist)"""
    albums = rpc('AudioLibrary.GetAlbums', {'filter': {'artistid': artistid}, 'properties': ['title', 'year', 'thumbnail', 'artist'],
                                            'sort': {'method': 'year', 'order': 'ascending'}}).get('albums') or []
    out = []
    for album in albums:
        if album['albumid'] == skip:
            continue
        item = xbmcgui.ListItem(label=album.get('title') or album.get('label') or '', offscreen=True)
        tag = item.getMusicInfoTag()
        tag.setMediaType('album')
        tag.setAlbum(album.get('title') or '')
        tag.setArtist(' / '.join(album.get('artist') or ()))
        if album.get('year'):
            tag.setYear(int(album['year']))
        tag.setDbId(int(album['albumid']), 'album')
        if album.get('thumbnail'):
            item.setArt({'thumb': album['thumbnail'], 'icon': album['thumbnail']})
        out.append(('musicdb://albums/%d/' % album['albumid'], item, True))
    return out


MOVIE_PROPERTIES = ['title', 'year', 'plot', 'rating', 'genre', 'runtime', 'mpaa', 'premiered', 'playcount', 'resume', 'file', 'art',
                    'studio', 'tagline', 'votes', 'streamdetails', 'uniqueid', 'director']
SHOW_PROPERTIES = ['title', 'year', 'plot', 'rating', 'genre', 'mpaa', 'premiered', 'playcount', 'episode', 'watchedepisodes', 'season',
                   'art', 'studio', 'votes', 'uniqueid']
ONLINE_PROPERTIES = ['title', 'year', 'plot', 'rating', 'art', 'genre', 'premiered', 'firstaired', 'uniqueid', 'mpaa', 'runtime', 'votes', 'studio']


def common_tag(item, details, media):
    tag = item.getVideoInfoTag()
    tag.setMediaType(media)
    tag.setTitle(details.get('title') or details.get('label') or '')
    if details.get('year'):
        tag.setYear(int(details['year']))
    tag.setPlot(details.get('plot') or '')
    if details.get('rating'):
        tag.setRating(float(details['rating']), int(details.get('votes') or 0))
    tag.setGenres(list(details.get('genre') or ()))
    tag.setMpaa(details.get('mpaa') or '')
    tag.setStudios(list(details.get('studio') or ()))
    premiered = details.get('premiered') or details.get('firstaired') or ''
    if premiered:
        tag.setPremiered(premiered[:10])
    ids = {key: str(value) for key, value in (details.get('uniqueid') or {}).items() if value}
    if ids:
        tag.setUniqueIDs(ids, 'tmdb' if 'tmdb' in ids else list(ids)[0])
    art = {key: value for key, value in (details.get('art') or {}).items() if value}
    if art:
        item.setArt(art)
    return tag


def library_movie(movieid):
    details = rpc('VideoLibrary.GetMovieDetails', {'movieid': movieid, 'properties': MOVIE_PROPERTIES}).get('moviedetails')
    if not details:
        return None
    item = xbmcgui.ListItem(label=details.get('title') or details.get('label') or '', offscreen=True)
    tag = common_tag(item, details, 'movie')
    tag.setDbId(movieid)
    tag.setDuration(int(details.get('runtime') or 0))
    tag.setTagLine(details.get('tagline') or '')
    tag.setDirectors(list(details.get('director') or ()))
    tag.setPlaycount(int(details.get('playcount') or 0))
    resume = details.get('resume') or {}
    if resume.get('position'):
        tag.setResumePoint(float(resume['position']), float(resume.get('total') or 0))
    streams = details.get('streamdetails') or {}
    try:
        for video in streams.get('video') or ():
            tag.addVideoStream(xbmc.VideoStreamDetail(width=int(video.get('width') or 0), height=int(video.get('height') or 0),
                                                      aspect=float(video.get('aspect') or 0), codec=video.get('codec') or '',
                                                      duration=int(video.get('duration') or 0), hdrtype=video.get('hdrtype') or ''))
        for audio in streams.get('audio') or ():
            tag.addAudioStream(xbmc.AudioStreamDetail(channels=int(audio.get('channels') or 0), codec=audio.get('codec') or '',
                                                      language=audio.get('language') or ''))
    except (TypeError, AttributeError):
        pass
    item.setProperty('aeon.owned', '1')
    return details['file'], item, False


def library_show(tvshowid):
    details = rpc('VideoLibrary.GetTVShowDetails', {'tvshowid': tvshowid, 'properties': SHOW_PROPERTIES}).get('tvshowdetails')
    if not details:
        return None
    item = xbmcgui.ListItem(label=details.get('title') or details.get('label') or '', offscreen=True)
    tag = common_tag(item, details, 'tvshow')
    tag.setDbId(tvshowid)
    tag.setPlaycount(int(details.get('playcount') or 0))
    total = int(details.get('episode') or 0)
    watched = int(details.get('watchedepisodes') or 0)
    item.setProperty('TotalEpisodes', str(total))
    item.setProperty('WatchedEpisodes', str(watched))
    item.setProperty('UnWatchedEpisodes', str(max(0, total - watched)))
    item.setProperty('TotalSeasons', str(int(details.get('season') or 0)))
    if total:
        item.setProperty('WatchedEpisodePercent', str(int(round(100.0 * watched / total))))
    item.setProperty('aeon.owned', '1')
    return 'videodb://tvshows/titles/%d/' % tvshowid, item, True


def online_missing(entry, media, bare=False):
    """A title that is not in the library. bare: name, year and pictures only, no video details - Kodi's information
    window opens the information of any video item that is clicked inside it, and there is nothing to open here."""
    title = matching.plain(entry.get('title') or entry.get('label'))
    item = xbmcgui.ListItem(label=title, offscreen=True)
    if bare:
        year = matching.year_of(entry)
        item.setProperty('year', str(year) if year else '')
        art = {key: value for key, value in (entry.get('art') or {}).items() if value}
        if art:
            item.setArt(art)
    else:
        details = dict(entry)
        details['title'] = title
        common_tag(item, details, media)
    item.setProperty('aeon.missing', '1')
    return NOOP, item, False


def online_list(name, kind, query, year, bare=False):
    origin = matching.origin_of(xbmc.getInfoLabel('Skin.String(aeon.cinema.country)'))   # Skin settings > Spotlight & widgets
    source = matching.build_path(name, kind, query, year, origin)
    if not source or not xbmc.getCondVisibility('System.AddonIsEnabled(plugin.video.themoviedb.helper)'):
        return []
    files = rpc('Files.GetDirectory', {'directory': source, 'media': 'video', 'properties': ONLINE_PROPERTIES}).get('files') or []
    library = videocache.load()
    if library is None:
        library = videocache.build() or {}
    by_tmdb, by_title = matching.index(library.get(kind) or (), 'dbid')
    media = 'movie' if kind == 'movie' else 'tvshow'
    items = []
    for entry in files:
        if entry.get('type') not in ('movie', 'tvshow'):
            continue                        # "next page" and other folders of the add-on
        dbid = matching.find(entry, by_tmdb, by_title)
        made = (library_movie(dbid) if kind == 'movie' else library_show(dbid)) if dbid else None
        items.append(made or online_missing(entry, media, bare))
    return items


RELEASE_WORDS = {'cinema': 32038, 'cinemanow': 32039, 'digital': 32040, 'physical': 32041, 'newshow': 32042, 'album': 32043}


def planner_item(entry, day='', daydate='', inlib=False):
    """An upcoming episode, film or album: nothing to play, so it is plain information for the skin. Wanted titles of
    the Planner sources carry aeon.source and aeon.release, with their words in aeon.releasetext (In cinemas now ...)."""
    kind = entry.get('kind') or 'episode'
    film = kind == 'movie'
    album = kind == 'album'
    item = xbmcgui.ListItem(label=entry.get('title') or '', offscreen=True)
    item.setProperty('day', day)
    item.setProperty('daydate', daydate)
    item.setProperty('kind', kind)
    release = entry.get('release') or ''
    if entry.get('source'):
        item.setProperty('aeon.source', entry['source'])
        item.setProperty('aeon.release', release)
        word = RELEASE_WORDS.get(release)
        item.setProperty('aeon.releasetext', xbmcaddon.Addon('script.aeon.helper').getLocalizedString(word) if word else '')
    # 0.3.97: series / season premiere, (mid-season) season / series finale
    epkind = planner.entry_kind(entry)          # a list kept from before 0.3.97: the premieres from the numbers
    item.setProperty('aeon.epkind', epkind)
    item.setProperty('aeon.epkindtext', xbmcaddon.Addon('script.aeon.helper').getLocalizedString(planner.EPKIND_WORDS[epkind]) if epkind in planner.EPKIND_WORDS else '')
    if album:
        item.setProperty('aeon.artist', entry.get('artist') or '')
        item.setLabel2(entry.get('artist') or '')
    tag = item.getVideoInfoTag()
    tag.setMediaType('movie' if film or album else 'episode')
    tag.setTitle(entry.get('title') or '')
    if entry.get('year'):
        tag.setYear(int(entry['year']))
    if not film and not album:
        tag.setTvShowTitle(entry.get('showtitle') or '')
        tag.setSeason(int(entry.get('season') or 0))
        tag.setEpisode(int(entry.get('episode') or 0))
        tag.setFirstAired(entry['premiered'])
    tag.setPremiered(entry['premiered'])
    more = entry.get('more') or {}
    tag.setPlot(planner.text_or_empty(entry.get('plot')) or planner.text_or_empty(more.get('showplot')))
    # the episode's own title for the spotlights (Season 2 · Episode 2 · <title>), empty when it is only "Episode 2"
    item.setProperty('aeon.eptitle', '' if film or album else planner.real_episode_title(entry.get('title')))
    tag.setDuration(int(entry.get('runtime') or 0))
    if more.get('genre'):
        tag.setGenres(list(more['genre']))
    if more.get('studio'):
        tag.setStudios(list(more['studio']))
    if more.get('mpaa'):
        tag.setMpaa(more['mpaa'])
    if more.get('rating'):
        tag.setRating(float(more['rating']), int(more.get('votes') or 0), 'tmdb', True)
    if more.get('cast'):
        tag.setCast([xbmc.Actor(actor['name'], actor.get('role') or '', number, actor.get('thumbnail') or '') for number, actor in enumerate(more['cast'])])
    item.setProperty('network', more.get('network') or '')
    art = dict(entry.get('art') or {})
    if 'thumb' not in art:
        for name in ('still', 'landscape', 'tvshow.landscape', 'fanart', 'tvshow.fanart'):
            if art.get(name):
                art['thumb'] = art[name]
                break
    if art:
        item.setArt(art)
    item.setProperty('aeon.missing', '1')
    # 0.3.58: already in the library (the Planner window marks it 'Available in library')
    item.setProperty('aeon.inlib', '1' if inlib else '')
    return NOOP, item, False


def planner_what():
    value = xbmc.getInfoLabel('Skin.String(aeon.planner.what)')
    return value if value in ('episodes', 'films') else ''


def next_aired(days=None, what=None):
    """The whole calendar in one list (Home strips, the Planner spotlight). days: today and that many days ahead.
    what: '' both, 'episodes', 'films'; None = as chosen in the Planner window."""
    what = planner_what() if what is None else (what if what in ('episodes', 'films') else '')
    episodes = nextaired.upcoming(days=days, what=what)
    words = {'today': xbmc.getLocalizedString(33006), 'tomorrow': xbmc.getLocalizedString(33007),
             'weekdays': [xbmc.getLocalizedString(number) for number in range(11, 18)]}
    months = [xbmc.getLocalizedString(number) for number in range(21, 33)]
    heads = planner.headings([entry['premiered'] for entry in episodes], datetime.date.today(), words, months)
    today = datetime.date.today()
    items = []
    for entry, (day, daydate) in zip(episodes, heads):
        made = planner_item(entry, day, daydate)
        date = planner.parse(entry['premiered'])
        # every item says when: 'Today  11 Nov', 'Friday  13 Nov'
        made[1].setProperty('when', '%s  %d %s' % (planner.day_label(date, today, words), date.day, months[date.month - 1][:3]) if date else '')
        items.append(made)
    return items


def screensaver_dress(entry, item):
    """Airing today / tomorrow on the screensaver (screensaver.aeon.fuse 1.2.0, ss=1): the show's poster, backdrop and
    logo where the episode has none of its own, the show's name as the title, "S3 E5 - <title>" in aeon.ss.line1 and the
    network in aeon.ss.line2."""
    art = entry.get('art') or {}
    fill = {}
    for key, others in (('poster', ('season.poster', 'tvshow.poster')), ('fanart', ('tvshow.fanart', 'landscape', 'tvshow.landscape')),
                        ('clearlogo', ('tvshow.clearlogo',))):
        if not art.get(key):
            for other in others:
                if art.get(other):
                    fill[key] = art[other]
                    break
    if fill:
        item.setArt(fill)
    kind = entry.get('kind') or 'episode'
    if kind == 'episode':
        if entry.get('showtitle'):
            item.setLabel(entry['showtitle'])
        title = planner.real_episode_title(entry.get('title'))
        item.setProperty('aeon.ss.line1', favspot.episode_tag(entry.get('season'), entry.get('episode')) + (DOT + title if title else ''))
    elif kind == 'album':
        item.setProperty('aeon.ss.line1', entry.get('artist') or '')
    item.setProperty('aeon.ss.line2', (entry.get('more') or {}).get('network') or '')


def planner_day(date, ss=False):
    """What is planned on one day (a list of the Planner window; ss: dressed for the screensaver)."""
    today = datetime.date.today()
    wanted = planner.parse(date)
    if wanted is None:
        return []
    if wanted < today:
        # Earlier days (0.3.76): what aired on the days before today in this week, from the library
        import plannerwin
        if not plannerwin.earlier_on() or wanted < plannerwin.week_first(today) or planner_what() == 'films':
            return []
        # the week's aired episodes as the Planner window counted them (cached, 0.3.78), this day's
        day = planner.group(plannerwin.aired_on(wanted, today), wanted).get(wanted) or ()
    else:
        entries = nextaired.kept(planner_what())
        day = planner.group(entries, today).get(wanted) or ()
    watching = xbmc.getCondVisibility('Skin.HasSetting(aeon.planner.watching)')
    fused = xbmc.getCondVisibility('Skin.HasSetting(aeon.fglass)')
    shows = None
    titles = sorted(set(e.get('showtitle') for e in day if (e.get('kind') or 'episode') == 'episode' and e.get('showtitle')))
    if titles and (watching or fused):
        # only the shows of this day, in one query (0.3.74: Shows you watch and "You're on S3 E1")
        rule = {'or': [{'field': 'title', 'operator': 'is', 'value': title} for title in titles]}
        shows = rpc('VideoLibrary.GetTVShows', {'filter': rule, 'properties': ['title', 'watchedepisodes']}).get('tvshows') or []
    if watching:
        day = planner.only_watched(day, [s.get('title') or '' for s in shows or () if s.get('watchedepisodes')])
    look = inlibrary.Lookup(rpc)
    look.prefetch(day)
    items = [planner_item(entry, inlib=look.has(entry)) for entry in day]
    if ss:
        for entry, made in zip(day, items):
            screensaver_dress(entry, made[1])
        return items
    if shows and fused:
        # Fused Glass (0.3.74): "You're on S3 E1" on an episode of a library show you are behind on
        ids = dict(((s.get('title') or '').strip().lower(), s['tvshowid']) for s in shows if s.get('watchedepisodes'))
        known = {}
        pattern = FavSpot().text(32518, "You're on {episode}")
        for entry, made in zip(day, items):
            key = (entry.get('showtitle') or '').strip().lower()
            if (entry.get('kind') or 'episode') != 'episode' or key not in ids:
                continue
            if key not in known:
                eps = rpc('VideoLibrary.GetEpisodes', {'tvshowid': ids[key], 'properties': ['season', 'episode', 'playcount', 'resume',
                                                                                         'lastplayed']}).get('episodes') or []
                chosen, _started, _more = favspot.continue_episode(eps)
                known[key] = (chosen.get('season'), chosen.get('episode')) if chosen else None
            if planner.behind(known[key], entry):
                made[1].setProperty('aeon.pl.on', favspot.fill(pattern, episode=favspot.episode_tag(*known[key])))
    return items


def reload_menu():
    """?info=reloadmenu - after a Home menu file of script.skinvariables was changed outside Kodi."""
    menufile.reload()


CHANNEL_PROPERTIES = ['thumbnail', 'icon', 'channelnumber', 'lastplayed', 'broadcastnow', 'broadcastnext']


def channel_list(group, limit):
    """Live TV on Home. group '' / 'last' = the channels watched last; a number = the channels of that group.
    OK on one plays it (?info=playchannel)."""
    if group.isdigit():
        found = rpc('PVR.GetChannels', {'channelgroupid': int(group), 'properties': CHANNEL_PROPERTIES, 'limits': {'end': limit}}).get('channels') or []
    else:
        found = channels.last_played(rpc('PVR.GetChannels', {'channelgroupid': 'alltv', 'properties': CHANNEL_PROPERTIES}).get('channels'), limit)
    items = []
    for channel in found:
        info = channels.describe(channel)
        item = xbmcgui.ListItem(label=info['label'], label2=info['now'], offscreen=True)
        for key in ('now', 'next', 'plot', 'progress', 'number'):
            item.setProperty(key, info[key])
        if info['icon']:
            item.setArt({'thumb': info['icon'], 'icon': info['icon']})
        items.append(('plugin://script.aeon.helper/?info=playchannel&id=%d' % info['channelid'], item, False))
    return items


FAV_WORDS = {'tvshow': 20364, 'episode': 20359, 'movie': 20338, 'set': 20457, 'album': 558, 'artist': 557, 'channel': 19029,
             'addon': 24000, 'song': 179, 'file': 20338, 'folder': 20334, 'window': 1036}
FAV_DETAILS = {
    'tvshow': ('VideoLibrary.GetTVShowDetails', 'tvshowid', 'tvshowdetails', ['art', 'plot', 'year', 'genre', 'studio', 'title']),
    'movie': ('VideoLibrary.GetMovieDetails', 'movieid', 'moviedetails', ['art', 'plot', 'year', 'genre', 'studio', 'resume', 'runtime']),
    'episode': ('VideoLibrary.GetEpisodeDetails', 'episodeid', 'episodedetails', ['art', 'plot', 'title', 'showtitle', 'season', 'episode',
                                                                                 'resume', 'runtime', 'tvshowid', 'firstaired']),
    'set': ('VideoLibrary.GetMovieSetDetails', 'setid', 'setdetails', ['art', 'plot']),
    'album': ('AudioLibrary.GetAlbumDetails', 'albumid', 'albumdetails', ['art', 'description', 'year', 'genre', 'displayartist']),
    'artist': ('AudioLibrary.GetArtistDetails', 'artistid', 'artistdetails', ['art', 'description', 'genre']),
}
SKIN = 'skin.aeon.fuse'
FAV_PLAY = 'RunPlugin(plugin://script.aeon.helper/?info=favplay&type=%s&id=%d&mode=%s)'
DOT = u' \u00b7 '


class FavSpot(object):
    """Fused Glass Home > Favourites (0.3.73): the tile (aeon.favshape / aeon.favart / aeon.favglyph / aeon.favby /
    aeon.favnow) and the spotlight of each favourite: aeon.fav.mode = spot (OK moves to the spotlight's buttons; else OK
    opens the favourite), aeon.fav.ep ("Continue S3 E1 - Marnukh"), aeon.fav.left ("38 min left"), aeon.fav.started,
    aeon.fav.next ("S3 E5 airs Wednesday 18 November - 3 more waiting in season 3"), the buttons aeon.fav.l1 / a1,
    l2 / a2, l3 / a3 (label / builtin) and aeon.fav.info (builtin). The resume point goes on the item (PercentPlayed)."""

    def __init__(self):
        self.today = datetime.date.today()
        self._skin = None
        self._aired = None
        self._channels = None

    def text(self, ident, default):
        try:
            if self._skin is None:
                self._skin = xbmcaddon.Addon(SKIN)
            return self._skin.getLocalizedString(ident) or default
        except Exception:
            return default

    def aired(self):
        if self._aired is None:
            try:
                self._aired = nextaired.kept('episodes')
            except Exception:
                self._aired = []
        return self._aired

    def channel(self, title):
        if self._channels is None:
            found = []
            for group in ('alltv', 'allradio'):
                try:
                    found += rpc('PVR.GetChannels', {'channelgroupid': group, 'properties': ['broadcastnow', 'broadcastnext', 'channelnumber', 'icon', 'thumbnail']}).get('channels') or []
                except Exception:
                    pass
            self._channels = dict(((c.get('label') or '').strip().lower(), c) for c in found)
        return self._channels.get((title or '').strip().lower())

    def decorate(self, item, fav, what, dbid, details, art):
        thumb = fav.get('thumbnail') or ''
        path = favourites.target(fav)
        item.setProperty('aeon.favshape', favspot.shape(what))
        pic = favspot.tile_art(what, art, thumb)
        if pic and ('/' in pic or '\\' in pic):
            item.setProperty('aeon.favart', pic)
        else:
            glyph = 'playlist' if favspot.is_playlist(path) else what
            item.setProperty('aeon.favglyph', favspot.GLYPHS.get(glyph, 'aeon/icons/grid.png'))
        if what == 'channel':
            found = self.channel(fav.get('title'))
            if found:
                item.setProperty('aeon.favby', str(found.get('channelnumber') or ''))
                item.setProperty('aeon.favnow', (found.get('broadcastnow') or {}).get('title') or '')
                logo = found.get('icon') or found.get('thumbnail') or ''
                if logo:                                     # the channel's logo, not a TV glyph (0.3.76)
                    item.setProperty('aeon.favart', logo)
                    item.setProperty('aeon.favglyph', '')
                    item.setArt({'clearlogo': logo})         # and in the spotlight, over Now / Next
                now, after = found.get('broadcastnow') or {}, found.get('broadcastnext') or {}
                lines = []
                if now.get('title'):
                    lines.append('[B]%s: %s[/B]' % (xbmc.getLocalizedString(19030), now['title']))
                if after.get('title'):
                    lines.append('%s: %s' % (xbmc.getLocalizedString(19031), after['title']))
                if now.get('plot'):                          # last, so a long plot never pushes Next out
                    lines.append(now['plot'])
                if lines:
                    item.getVideoInfoTag().setPlot('[CR]'.join(lines))
        if what == 'album':
            item.setProperty('aeon.favby', details.get('displayartist') or '')
        if not dbid or what not in ('tvshow', 'episode', 'movie', 'album', 'artist'):
            return
        item.setProperty('aeon.fav.mode', 'spot')
        item.setProperty('aeon.fav.info', 'RunPlugin(plugin://script.aeon.helper/?info=favinfo&type=%s&id=%d)' % (what, dbid))
        resume, play, start = xbmc.getLocalizedString(13404), xbmc.getLocalizedString(208), xbmc.getLocalizedString(12021)
        if what == 'tvshow':
            self.show(item, dbid, details, resume, play, start)
        elif what == 'episode':
            self.episode(item, dbid, details, resume, play, start)
        elif what == 'movie':
            pct, left = favspot.progress(details)
            started = pct > 0
            if started:
                self.progress(item, details, left)
                item.setProperty('aeon.fav.ep', self.text(32071, 'Continue'))
            item.setProperty('aeon.fav.l1', resume if started else play)
            item.setProperty('aeon.fav.a1', FAV_PLAY % ('movie', dbid, 'resume'))
            if started:
                item.setProperty('aeon.fav.l2', start)
                item.setProperty('aeon.fav.a2', FAV_PLAY % ('movie', dbid, 'start'))
        elif what == 'album':
            item.setProperty('aeon.fav.l1', play)
            item.setProperty('aeon.fav.a1', FAV_PLAY % ('album', dbid, 'play'))
            item.setProperty('aeon.fav.l2', xbmc.getLocalizedString(191))
            item.setProperty('aeon.fav.a2', FAV_PLAY % ('album', dbid, 'shuffle'))
        elif what == 'artist':
            item.setProperty('aeon.fav.l1', xbmc.getLocalizedString(191))
            item.setProperty('aeon.fav.a1', FAV_PLAY % ('artist', dbid, 'shuffle'))
            item.setProperty('aeon.fav.l3', xbmc.getLocalizedString(132))
            item.setProperty('aeon.fav.a3', 'ActivateWindow(Music,musicdb://artists/%d/,return)' % dbid)

    def progress(self, item, details, left):
        item.setProperty('aeon.fav.started', '1')
        if left:
            item.setProperty('aeon.fav.left', favspot.fill(self.text(32512, '{n} min left'), n=left))
        resume = details.get('resume') or {}
        total = float(resume.get('total') or 0) or float(details.get('runtime') or 0)
        if total:
            item.getVideoInfoTag().setResumePoint(float(resume.get('position') or 0), total)

    def episode(self, item, dbid, details, resume, play, start):
        """An episode saved as a file (0.3.76): its thumb under the show's logo, Continue / Play it, from the start, All
        episodes of its show and the show's next airing."""
        thumb = (details.get('art') or {}).get('thumb')
        if thumb:
            item.setProperty('aeon.fav.epthumb', thumb)
        tag = favspot.episode_tag(details.get('season'), details.get('episode'))
        pct, left = favspot.progress(details)
        started = pct > 0
        title = DOT + details['title'] if details.get('title') else ''
        item.setProperty('aeon.fav.ep', ('%s %s%s' % (self.text(32071, 'Continue'), tag, title)) if started else tag + title)
        if started:
            self.progress(item, details, left)
        elif left:
            item.setProperty('aeon.fav.left', favspot.fill(self.text(32512, '{n} min left'), n=left))
        item.setProperty('aeon.fav.l1', '%s %s' % (resume if started else play, tag))
        item.setProperty('aeon.fav.a1', FAV_PLAY % ('episode', dbid, 'resume'))
        if started:
            item.setProperty('aeon.fav.l2', start)
            item.setProperty('aeon.fav.a2', FAV_PLAY % ('episode', dbid, 'start'))
        if details.get('tvshowid'):
            item.setProperty('aeon.fav.l3', self.text(32510, 'All episodes'))
            item.setProperty('aeon.fav.a3', 'ActivateWindow(Videos,videodb://tvshows/titles/%d/,return)' % details['tvshowid'])
        airing = favspot.next_airing(self.aired(), details.get('showtitle') or '', self.today)
        if airing:
            weekdays = [xbmc.getLocalizedString(n) for n in range(11, 18)]
            months = [xbmc.getLocalizedString(n) for n in range(21, 33)]
            date = favspot.air_date(airing.get('premiered'), self.today, weekdays, months,
                                    {'today': xbmc.getLocalizedString(33006), 'tomorrow': xbmc.getLocalizedString(33007)})
            item.setProperty('aeon.fav.next', favspot.fill(self.text(32513, '{episode} airs {date}'),
                                                           episode=favspot.episode_tag(airing.get('season'), airing.get('episode')), date=date))

    def show(self, item, dbid, details, resume, play, start):
        episodes = rpc('VideoLibrary.GetEpisodes', {'tvshowid': dbid, 'properties': ['season', 'episode', 'title', 'playcount', 'resume',
                                                                                   'runtime', 'lastplayed', 'art']}).get('episodes') or []
        chosen, started, more = favspot.continue_episode(episodes)
        if chosen and (chosen.get('art') or {}).get('thumb'):
            item.setProperty('aeon.fav.epthumb', chosen['art']['thumb'])
        everything = 'ActivateWindow(Videos,videodb://tvshows/titles/%d/,return)' % dbid
        lines = []
        if chosen:
            tag = favspot.episode_tag(chosen.get('season'), chosen.get('episode'))
            item.setProperty('aeon.fav.ep', '%s %s%s' % (self.text(32071, 'Continue'), tag, DOT + chosen['title'] if chosen.get('title') else ''))
            _pct, left = favspot.progress(chosen)
            if started:
                self.progress(item, chosen, left)
            elif left:
                item.setProperty('aeon.fav.left', favspot.fill(self.text(32512, '{n} min left'), n=left))
            item.setProperty('aeon.fav.l1', '%s %s' % (resume if started else play, tag))
            item.setProperty('aeon.fav.a1', FAV_PLAY % ('episode', chosen['episodeid'], 'resume'))
            if started:
                item.setProperty('aeon.fav.l2', start)
                item.setProperty('aeon.fav.a2', FAV_PLAY % ('episode', chosen['episodeid'], 'start'))
            item.setProperty('aeon.fav.l3', self.text(32510, 'All episodes'))
            item.setProperty('aeon.fav.a3', everything)
        else:
            item.setProperty('aeon.fav.l1', self.text(32510, 'All episodes'))
            item.setProperty('aeon.fav.a1', everything)
        airing = favspot.next_airing(self.aired(), details.get('title') or item.getLabel(), self.today)
        if airing:
            weekdays = [xbmc.getLocalizedString(n) for n in range(11, 18)]
            months = [xbmc.getLocalizedString(n) for n in range(21, 33)]
            date = favspot.air_date(airing.get('premiered'), self.today, weekdays, months,
                                    {'today': xbmc.getLocalizedString(33006), 'tomorrow': xbmc.getLocalizedString(33007)})
            lines.append(favspot.fill(self.text(32513, '{episode} airs {date}'),
                                      episode=favspot.episode_tag(airing.get('season'), airing.get('episode')), date=date))
        if chosen and more:
            pattern = self.text(32515, '1 more waiting in season {season}') if more == 1 else self.text(32514, '{n} more waiting in season {season}')
            lines.append(favspot.fill(pattern, n=more, season=chosen.get('season')))
        item.setProperty('aeon.fav.next', DOT.join(lines))


def favourite_list(kind, channels=True):
    favs = rpc('Favourites.GetFavourites', {'properties': ['window', 'windowparameter', 'thumbnail', 'path']}).get('favourites') or []
    items = []
    spot = FavSpot()
    for index, fav in favourites.wanted(favs, kind, channels):
        group, what, dbid = favourites.classify(fav)
        if what == 'file' and group == 'video':
            # a film saved as a file: find it in the library by its file name, for its artwork and plot
            name = favourites.target(fav).replace('\\', '/').rsplit('/', 1)[-1]
            found = []
            if name:
                found = rpc('VideoLibrary.GetMovies', {'filter': {'field': 'filename', 'operator': 'is', 'value': name},
                                                       'limits': {'start': 0, 'end': 1}}).get('movies') or []
            if found:
                what, dbid = 'movie', found[0]['movieid']
            elif name:                         # else an episode of a library show (0.3.76)
                found = rpc('VideoLibrary.GetEpisodes', {'filter': {'field': 'filename', 'operator': 'is', 'value': name},
                                                         'limits': {'start': 0, 'end': 1}}).get('episodes') or []
                if found:
                    what, dbid = 'episode', found[0]['episodeid']
        details = {}
        if dbid and what in FAV_DETAILS:
            method, key, field, props = FAV_DETAILS[what]
            details = rpc(method, {key: dbid, 'properties': props}).get(field) or {}
        art = dict(details.get('art') or {})
        if what == 'episode':                  # the show's logo, backdrop and landscape for the spotlight
            for key in ('clearlogo', 'fanart', 'landscape', 'poster'):
                if not art.get(key):
                    art[key] = art.get('tvshow.%s' % key) or (art.get('season.poster') if key == 'poster' else '') or ''
        thumb = fav.get('thumbnail') or ''
        art.setdefault('thumb', thumb or art.get('poster', ''))
        art.setdefault('icon', thumb)
        item = xbmcgui.ListItem(fav.get('title') or '', xbmc.getLocalizedString(FAV_WORDS.get(what, 1036)), offscreen=True)
        item.setArt(art)
        item.setProperty('aeon.favwhat', what)
        item.setProperty('aeon.favgroup', group)
        tag = item.getVideoInfoTag()
        tag.setPlot(details.get('plot') or details.get('description') or '')
        if details.get('year'):
            tag.setYear(int(details['year']))
        if details.get('genre'):
            tag.setGenres(details['genre'] if isinstance(details['genre'], list) else [details['genre']])
        if details.get('studio'):
            tag.setStudios(details['studio'] if isinstance(details['studio'], list) else [details['studio']])
        try:
            spot.decorate(item, fav, what, dbid, details, art)
        except Exception as error:                 # a spotlight that cannot be read never hides the favourite
            xbmc.log('[script.aeon.helper] favourite spotlight %s: %s' % (fav.get('title'), error), xbmc.LOGINFO)
        items.append(('plugin://script.aeon.helper/?info=runfav&n=%d' % index, item, False))
    return items


def play_favourite(kind, ident, mode):
    """The spotlight's buttons (Fused Glass Home > Favourites): resume / start an episode or film, play or shuffle an
    album, shuffle an artist."""
    key = {'episode': 'episodeid', 'movie': 'movieid', 'album': 'albumid', 'artist': 'artistid'}.get(kind)
    if not key or not ident:
        return
    options = {}
    if kind in ('episode', 'movie'):
        options['resume'] = mode == 'resume'
    if mode == 'shuffle':
        options['shuffled'] = True
    rpc('Player.Open', {'item': {key: ident}, 'options': options})


INFO_DETAILS = {
    'tvshow': ('VideoLibrary.GetTVShowDetails', 'tvshowid', 'tvshowdetails', 'videodb://tvshows/titles/%d/'),
    'movie': ('VideoLibrary.GetMovieDetails', 'movieid', 'moviedetails', 'videodb://movies/titles/%d'),
    'episode': ('VideoLibrary.GetEpisodeDetails', 'episodeid', 'episodedetails', 'videodb://tvshows/titles/-1/-1/%d'),
    'album': ('AudioLibrary.GetAlbumDetails', 'albumid', 'albumdetails', 'musicdb://albums/%d/'),
    'artist': ('AudioLibrary.GetArtistDetails', 'artistid', 'artistdetails', 'musicdb://artists/%d/'),
}


def favourite_info(kind, ident):
    """Kodi's information dialog for a library show, film, album or artist (the spotlight's info button)."""
    if kind not in INFO_DETAILS or not ident:
        return
    method, key, field, path = INFO_DETAILS[kind]
    music = kind in ('album', 'artist')
    props = ['art'] if music else ['title', 'art']
    details = rpc(method, {key: ident, 'properties': props}).get(field) or {}
    item = xbmcgui.ListItem(details.get('title') or details.get('label') or '', path=path % ident, offscreen=True)
    item.setArt(details.get('art') or {})
    if music:
        tag = item.getMusicInfoTag()
        tag.setDbId(ident, kind)
        tag.setTitle(details.get('label') or '')
    else:
        tag = item.getVideoInfoTag()
        tag.setDbId(ident)
        tag.setMediaType(kind)
        tag.setTitle(details.get('title') or '')
    xbmcgui.Dialog().info(item)


def recent_sets(count):
    """?info=recentsets (0.3.77): the sets whose films were played last, newest first, as library set folders (one
    JSON-RPC call: Kodi's own Sets list by last played, see resources/lib/recentsets.py)."""
    from resources.lib import recentsets
    files = rpc('Files.GetDirectory', recentsets.request(count)).get('files') or []
    items = []
    for found in recentsets.played(files, count):
        item = xbmcgui.ListItem(found['label'], offscreen=True)
        item.setArt(found['art'])
        tag = item.getVideoInfoTag()
        tag.setMediaType('set')                              # ListItem.DBType set + DBID: the spotlight's film strip
        tag.setDbId(found['setid'])
        tag.setTitle(found['label'])
        tag.setPlot(found['plot'])
        tag.setLastPlayed(found['lastplayed'])               # a list sorted by last played keeps this order
        tag.setPlaycount(found['playcount'])
        items.append((found['path'], item, True))
    return items


def picture_folders():
    """?info=picfolders (0.3.98): Home > Pictures' row of folders, newest first, and the spotlight's properties."""
    from resources.lib import picfolders as pf
    home = xbmcgui.Window(10000)
    sources = rpc('Files.GetSources', {'media': 'pictures'}).get('sources') or []
    folder = xbmcvfs.translatePath('special://profile/addon_data/script.aeon.helper/')
    if not xbmcvfs.exists(folder):
        xbmcvfs.mkdirs(folder)
    path = os.path.join(folder, 'picfolders.json')
    try:
        with open(path, 'r') as f:
            cache = json.load(f)
    except (IOError, OSError, ValueError):
        cache = None
    folders = pf.fresh(cache, sources, time.time())
    if folders is None:
        def listdir(where):
            return rpc('Files.GetDirectory', {'directory': where, 'media': 'pictures',
                                              'properties': ['lastmodified', 'mimetype']}).get('files') or []
        began = time.time()
        folders = pf.walk(listdir, sources)
        xbmc.log('[script.aeon.helper] pictures: %d folders in %.1f s' % (len(folders), time.time() - began), xbmc.LOGINFO)
        try:
            with open(path, 'w') as f:
                json.dump({'key': pf.sources_key(sources), 'at': time.time(), 'folders': folders}, f)
        except (IOError, OSError):
            pass
    months = [xbmc.getLocalizedString(51 + i) for i in range(12)]
    for key, value in pf.spotlight(folders, months).items():
        home.setProperty('aeon.pic.' + key, value)
    home.setProperty('aeon.pic.sources', str(len([s for s in sources if pf.usable(s)])))
    home.setProperty('aeon.pic.done', '1')
    items = []
    for f in folders[:30]:
        item = xbmcgui.ListItem(f['name'], f['parent'], offscreen=True)
        if f['pictures']:
            item.setArt({'thumb': f['pictures'][0]})
        item.setProperties({'photos': str(f['photos']), 'videos': str(f['videos']), 'count': str(f['photos'] + f['videos']),
                            'dates': pf.date_range(f['oldest'], f['newest'], months)})
        items.append(('plugin://script.aeon.helper/?info=picopen&path=' + quote(f['path'], safe=''), item, False))
    item = xbmcgui.ListItem(xbmc.getLocalizedString(1), offscreen=True)                    # "Pictures": the window itself
    item.setProperty('aeon.pic.all', '1')
    items.append(('plugin://script.aeon.helper/?info=picopen', item, False))
    return items


EPISODE_PROPERTIES = ['title', 'plot', 'votes', 'rating', 'writer', 'firstaired', 'playcount', 'runtime', 'director', 'season', 'episode',
                      'showtitle', 'streamdetails', 'lastplayed', 'file', 'resume', 'tvshowid', 'dateadded', 'uniqueid', 'art']


def season_episodes(tvshowid, season):
    """?info=episodes (0.3.100): the season's episodes, those of one file in one row."""
    from resources.lib import multiep
    params = {'tvshowid': tvshowid, 'properties': EPISODE_PROPERTIES}
    if season >= 0:
        params['season'] = season
    episodes = rpc('VideoLibrary.GetEpisodes', params).get('episodes') or []
    style = xbmc.getInfoLabel('Skin.String(aeon.epcode)')
    # what a library episode takes from its show (Kodi keeps no certificate, genre or studio per episode)
    show = rpc('VideoLibrary.GetTVShowDetails', {'tvshowid': tvshowid, 'properties': ['mpaa', 'genre', 'studio']}).get('tvshowdetails') or {}
    items = []
    for parts in multiep.groups(episodes):
        first = parts[0]
        joined = len(parts) > 1
        title = multiep.join_title(parts) if joined else (first.get('title') or first.get('label') or '')
        item = xbmcgui.ListItem(multiep.label(parts, title), offscreen=True)
        tag = item.getVideoInfoTag()
        tag.setMediaType('episode')
        tag.setDbId(int(first['episodeid']))
        tag.setTitle(title)
        tag.setTvShowTitle(first.get('showtitle') or '')
        tag.setSeason(int(first.get('season') or 0))
        tag.setEpisode(int(first.get('episode') or 0))
        tag.setPlot(multiep.join_plot(parts) if joined else (first.get('plot') or ''))
        tag.setMpaa(show.get('mpaa') or '')
        tag.setGenres(list(show.get('genre') or ()))
        tag.setStudios(list(show.get('studio') or ()))
        if first.get('firstaired'):
            tag.setFirstAired(first['firstaired'])
        tag.setDuration(multiep.runtime(parts) if joined else int(first.get('runtime') or 0))
        if first.get('rating'):
            tag.setRating(float(first['rating']), int(first.get('votes') or 0))
        tag.setPlaycount(int(first.get('playcount') or 0))
        if first.get('lastplayed'):
            tag.setLastPlayed(first['lastplayed'])
        if first.get('dateadded'):
            tag.setDateAdded(first['dateadded'])
        tag.setDirectors(list(first.get('director') or ()))
        tag.setWriters(list(first.get('writer') or ()))
        ids = dict((k, str(v)) for k, v in (first.get('uniqueid') or {}).items() if v)
        if ids:
            tag.setUniqueIDs(ids, 'tmdb' if 'tmdb' in ids else list(ids)[0])
        resume = first.get('resume') or {}
        if resume.get('position'):
            tag.setResumePoint(float(resume['position']), float(resume.get('total') or 0))
        streams = first.get('streamdetails') or {}
        try:
            for video in streams.get('video') or ():
                tag.addVideoStream(xbmc.VideoStreamDetail(width=int(video.get('width') or 0), height=int(video.get('height') or 0),
                                                          aspect=float(video.get('aspect') or 0), codec=video.get('codec') or '',
                                                          duration=int(video.get('duration') or 0), hdrtype=video.get('hdrtype') or ''))
            for audio in streams.get('audio') or ():
                tag.addAudioStream(xbmc.AudioStreamDetail(channels=int(audio.get('channels') or 0), codec=audio.get('codec') or '',
                                                          language=audio.get('language') or ''))
            for subtitle in streams.get('subtitle') or ():
                tag.addSubtitleStream(xbmc.SubtitleStreamDetail(language=subtitle.get('language') or ''))
        except (TypeError, AttributeError):
            pass
        art = dict((k, v) for k, v in (first.get('art') or {}).items() if v)
        if art:
            item.setArt(art)
        item.setProperty('tvshowid', str(first.get('tvshowid') or tvshowid))
        if joined:
            item.setProperty('aeon.ep.range', multiep.numbers(parts))
            item.setProperty('aeon.ep.code', multiep.code(parts, style))
            item.setProperty('aeon.ep.count', str(len(parts)))
        items.append((first.get('file') or NOOP, item, False))
    return items


def album_item(album):
    """An album of the library for the screensaver: the cover, the artist's backdrop and logo, artist and year."""
    item = xbmcgui.ListItem(album.get('title') or album.get('label') or '', offscreen=True)
    tag = item.getMusicInfoTag()
    tag.setMediaType('album')
    tag.setDbId(int(album.get('albumid') or 0), 'album')
    tag.setTitle(album.get('title') or album.get('label') or '')
    tag.setAlbum(album.get('title') or album.get('label') or '')
    artist = album.get('artist') or []
    tag.setArtist(' / '.join(artist) if isinstance(artist, list) else artist)
    if album.get('year'):
        tag.setYear(int(album['year']))
    tag.setGenres(list(album.get('genre') or ()))
    art = dict((k, v) for k, v in (album.get('art') or {}).items() if v)
    art.setdefault('thumb', album.get('thumbnail') or '')
    for key in ('fanart', 'clearlogo'):
        if not art.get(key) and art.get('artist.' + key):
            art[key] = art['artist.' + key]
    item.setArt(dict((k, v) for k, v in art.items() if v))
    return NOOP, item, False


def round_pool(kind, count, rng):
    """Up to count random items of one source of the screensaver."""
    if kind == 'movies':
        found = rpc('VideoLibrary.GetMovies', {'sort': {'method': 'random'}, 'limits': {'end': count}}).get('movies') or []
        return [made for made in (library_movie(f['movieid']) for f in found) if made]
    if kind == 'tvshows':
        found = rpc('VideoLibrary.GetTVShows', {'sort': {'method': 'random'}, 'limits': {'end': count}}).get('tvshows') or []
        return [made for made in (library_show(f['tvshowid']) for f in found) if made]
    if kind == 'music':
        found = rpc('AudioLibrary.GetAlbums', {'sort': {'method': 'random'}, 'limits': {'end': count},
                                               'properties': ['title', 'artist', 'year', 'art', 'genre', 'thumbnail']}).get('albums') or []
        return [album_item(a) for a in found]
    if kind == 'cinema':
        got = list(online_list('now_playing', 'movie', '', ''))
    else:
        day = datetime.date.today() + datetime.timedelta(days=1 if kind == 'tomorrow' else 0)
        got = list(planner_day(day.isoformat(), ss=True))
    rng.shuffle(got)
    return got[:count]


def screensaver_round(count, kinds, number):
    """?info=ssround (0.3.98): one round of the screensaver, mixed from the sources asked for."""
    import random
    from resources.lib import ssround
    rng = random.Random()
    pools = {}
    for kind in kinds:
        try:
            pools[kind] = round_pool(kind, count, rng)
        except Exception as error:                        # one source failing leaves the others
            xbmc.log('[script.aeon.helper] screensaver round: %s: %s' % (kind, error), xbmc.LOGWARNING)
            pools[kind] = []
    items = []
    for kind, made in ssround.mix(pools, count, rng):
        made[1].setProperty('aeon.ss.kind', kind)
        items.append(made)
    home = xbmcgui.Window(10000)
    home.setProperty('aeon.ss.pages', str(len(items)))
    home.setProperty('aeon.ss.ready', number)
    return items


def open_pictures(path):
    """?info=picopen[&path=]: a folder card opens that folder in the Pictures window, the last card the window."""
    if path:
        xbmc.executebuiltin('ActivateWindow(Pictures,"%s",return)' % path.replace('"', '\\"'))
    else:
        xbmc.executebuiltin('ActivateWindow(Pictures)')


def run_favourite(index):
    favs = rpc('Favourites.GetFavourites', {'properties': ['window', 'windowparameter', 'thumbnail', 'path']}).get('favourites') or []
    if 0 <= index < len(favs):
        action = favourites.builtin(favs[index])
        if action:
            xbmc.executebuiltin(action)


def raw_params(text):
    """Query string -> dict; everything after &query= is the title, whatever it contains."""
    head, _mark, query = text.lstrip('?').partition('&query=')
    params = dict(parse_qsl(head))
    if query:
        params['query'] = unquote(query)
    return params


def main():
    handle = int(sys.argv[1])
    params = raw_params(sys.argv[2])
    info = params.get('info')
    items = []
    if info == 'playchannel' and params.get('id', '').isdigit():
        rpc('Player.Open', {'item': {'channelid': int(params['id'])}})
        return
    if info == 'runfav' and params.get('n', '').isdigit():
        run_favourite(int(params['n']))
        return
    if info == 'seasons':
        # plugin://script.aeon.helper/?info=seasons&path=<Container.FolderPath> (path last): Episode combined's pills (0.3.75)
        import epcomb
        items = epcomb.seasons(sys.argv[2].partition('&path=')[2])
        xbmcplugin.setContent(handle, 'seasons')
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'searchlib':
        # plugin://script.aeon.helper/?info=searchlib&type=all|tvshow|movie|people&q=<text>: library matches (0.3.73)
        import searchwin
        items = searchwin.library_items(params.get('type', 'all'), params.get('q', ''))
        xbmcplugin.setContent(handle, 'movies')
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'favplay':
        play_favourite(params.get('type', ''), int(params['id']) if params.get('id', '').isdigit() else 0, params.get('mode', ''))
        return
    if info == 'favinfo':
        favourite_info(params.get('type', ''), int(params['id']) if params.get('id', '').isdigit() else 0)
        return
    if info == 'favourites':
        items = favourite_list(params.get('kind', 'all'), params.get('chan') != '0')
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'channels':
        limit = int(params['limit']) if params.get('limit', '').isdigit() and int(params['limit']) > 0 else 20
        items = channel_list(params.get('group', ''), limit)
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'reloadmenu':
        reload_menu()
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'trim':
        # plugin://script.aeon.helper/?info=trim: hand freed C heap memory back to the system (Linux, glibc)
        import time
        from resources.lib import memtrim
        before, started = memtrim.rss_mb(), time.time()
        result = memtrim.trim()
        xbmc.log('[script.aeon.helper] malloc_trim: %s, Kodi %s MB -> %s MB (%.0f ms)'
                 % (result, before, memtrim.rss_mb(), (time.time() - started) * 1000), xbmc.LOGINFO)
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'playercast':
        # plugin://script.aeon.helper/?info=playercast[&dbtype=episode|movie&dbid=<id>]: the cast (default: of the video playing)
        # (Fused Glass information screen); label = name, label2 = character, art thumb = photo when it is a real path
        import playerfacts
        dbid = int(params['dbid']) if params.get('dbid', '').isdigit() else 0
        dbtype = params.get('dbtype', '')
        if not dbid:                                   # the video playing
            item = playerfacts.playing_item()
            dbtype, dbid = item.get('type', ''), item.get('id', 0) or 0
        for name, role, thumb in playerfacts.cast(dbtype, dbid):
            item = xbmcgui.ListItem(name, role, offscreen=True)
            if thumb:
                item.setArt({'thumb': thumb, 'icon': thumb})
            items.append((NOOP, item, False))
        xbmcplugin.setContent(handle, 'actors')
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'episodes' and params.get('tvshowid', '').isdigit():
        raw = params.get('season', '-1')
        season = int(raw) if raw.lstrip('-').isdigit() else -1
        items = season_episodes(int(params['tvshowid']), season)
        xbmcplugin.setContent(handle, 'episodes')
        if season >= 0:
            xbmcplugin.setPluginCategory(handle, '%s %d' % (xbmc.getLocalizedString(20373), season))
        # the label as the library writes it in a season, "01. LA X" (Kodi would make it "6x01. LA X"); %L keeps the
        # item's own label, which holds the joined range ("01-02. LA X")
        xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_EPISODE, labelMask='%L')
        xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_UNSORTED, labelMask='%L')
        # where Back goes (Kodi would open the helper's empty top level): the show's seasons, or the shows when the
        # show has one season (Kodi skips the seasons list then, and would open the episodes again)
        seasons = rpc('VideoLibrary.GetSeasons', {'tvshowid': int(params['tvshowid'])}).get('seasons') or []
        parent = 'videodb://tvshows/titles/' if season < 0 or len(seasons) < 2 else 'videodb://tvshows/titles/%d/' % int(params['tvshowid'])
        xbmcgui.Window(10000).setProperty('aeon.ep.parent', parent)
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'ssround':
        from resources.lib import ssround
        items = screensaver_round(ssround.count_of(params.get('n')), ssround.kinds_of(params.get('kinds')), params.get('r', ''))
        xbmcplugin.setContent(handle, 'videos')
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'picopen':
        open_pictures(unquote(params.get('path', '')))
        return
    if info == 'picfolders':
        items = picture_folders()
        xbmcplugin.setContent(handle, 'images')
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'recentsets':
        from resources.lib.recentsets import limit
        items = recent_sets(limit(params.get('limit')))
        xbmcplugin.setContent(handle, 'sets')
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'planner':
        items = planner_day(params.get('date', ''), ss=params.get('ss') == '1')
        xbmcplugin.setContent(handle, 'episodes')
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'nextaired':
        items = next_aired(int(params['days']) if params.get('days', '').isdigit() else None, params.get('what') if 'spot' in params else None)
        if params.get('limit', '').isdigit():          # the exact number asked for (a limit on the list itself gives one more)
            items = items[:int(params['limit'])]
        xbmcplugin.setContent(handle, 'episodes')
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info in ('peek', 'sources', 'substreams', 'audiostreams'):    # 0.3.118: round-3 Fused Glass style windows
        from resources.lib import round3
        if info == 'audiostreams':                   # 0.3.121: the File and season page of the player information
            items = round3.audiostreams()
        else:
            items = round3.peek_list() if info == 'peek' else (round3.sources_list(params.get('media')) if info == 'sources' else round3.substreams())
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'picstrip':                      # 0.3.117: Picture info's strip of the folder
        from resources.lib import fgsfacts
        items = fgsfacts.strip(params.get('path') or xbmcgui.Window(10000).getProperty('aeon.pic.path'))
        xbmcplugin.setContent(handle, 'images')
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if info == 'online':
        items = online_list(params.get('list'), params.get('type'), params.get('query', ''), params.get('year', ''), bare=params.get('bare') == '1')
        xbmcplugin.setContent(handle, 'movies' if params.get('type') == 'movie' else 'tvshows')
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    # 0.3.116: an album page (Fused Glass style Music information) names its album; the rows read its first artist
    albumid = int(params['albumid']) if params.get('albumid', '').isdigit() else 0
    if albumid and not params.get('artistid', '').isdigit():
        details = rpc('AudioLibrary.GetAlbumDetails', {'albumid': albumid, 'properties': ['artistid']}).get('albumdetails') or {}
        if details.get('artistid'):
            params['artistid'] = str(details['artistid'][0])
    if params.get('artistid', '').isdigit():
        artistid = int(params['artistid'])
        if info == 'toptracks':
            items = top_tracks(artistid)
        elif info == 'similar':
            items = similar_artists(artistid)
        elif info == 'albums':
            items = artist_albums(artistid, albumid)
    xbmcplugin.setContent(handle, 'artists' if info == 'similar' else ('albums' if info == 'albums' else 'songs'))
    xbmcplugin.addDirectoryItems(handle, items, len(items))
    xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)


if __name__ == '__main__':
    main()
