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
    from urllib.parse import parse_qsl, unquote
    from urllib.request import Request, urlopen
except ImportError:                      # pragma: no cover
    from urlparse import parse_qsl
    from urllib import unquote
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
from resources.lib import channels, deezer, favourites, inlibrary, planner, similar
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


MOVIE_PROPERTIES = ['title', 'year', 'plot', 'rating', 'genre', 'runtime', 'mpaa', 'premiered', 'playcount', 'resume', 'file', 'art',
                    'studio', 'tagline', 'votes', 'streamdetails', 'uniqueid']
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
    source = matching.build_path(name, kind, query, year)
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
    tag.setPlot(entry.get('plot') or more.get('showplot') or '')
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


def planner_day(date):
    """What is planned on one day (a list of the Planner window)."""
    today = datetime.date.today()
    wanted = planner.parse(date)
    if wanted is None or wanted < today:
        return []
    entries = nextaired.kept(planner_what())
    day = planner.group(entries, today).get(wanted) or ()
    look = inlibrary.Lookup(rpc)
    look.prefetch(day)
    return [planner_item(entry, inlib=look.has(entry)) for entry in day]


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


FAV_WORDS = {'tvshow': 20364, 'movie': 20338, 'set': 20457, 'album': 558, 'artist': 557, 'channel': 19029,
             'addon': 24000, 'song': 179, 'file': 20338, 'folder': 20334, 'window': 1036}
FAV_DETAILS = {
    'tvshow': ('VideoLibrary.GetTVShowDetails', 'tvshowid', 'tvshowdetails', ['art', 'plot', 'year', 'genre']),
    'movie': ('VideoLibrary.GetMovieDetails', 'movieid', 'moviedetails', ['art', 'plot', 'year', 'genre']),
    'set': ('VideoLibrary.GetMovieSetDetails', 'setid', 'setdetails', ['art', 'plot']),
    'album': ('AudioLibrary.GetAlbumDetails', 'albumid', 'albumdetails', ['art', 'description', 'year', 'genre']),
    'artist': ('AudioLibrary.GetArtistDetails', 'artistid', 'artistdetails', ['art', 'description', 'genre']),
}


def favourite_list(kind):
    favs = rpc('Favourites.GetFavourites', {'properties': ['window', 'windowparameter', 'thumbnail', 'path']}).get('favourites') or []
    items = []
    for index, fav in favourites.wanted(favs, kind):
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
        details = {}
        if dbid and what in FAV_DETAILS:
            method, key, field, props = FAV_DETAILS[what]
            details = rpc(method, {key: dbid, 'properties': props}).get(field) or {}
        art = dict(details.get('art') or {})
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
        items.append(('plugin://script.aeon.helper/?info=runfav&n=%d' % index, item, False))
    return items


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
    if info == 'favourites':
        items = favourite_list(params.get('kind', 'all'))
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
    if info == 'planner':
        items = planner_day(params.get('date', ''))
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
    if info == 'online':
        items = online_list(params.get('list'), params.get('type'), params.get('query', ''), params.get('year', ''), bare=params.get('bare') == '1')
        xbmcplugin.setContent(handle, 'movies' if params.get('type') == 'movie' else 'tvshows')
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    if params.get('artistid', '').isdigit():
        artistid = int(params['artistid'])
        if info == 'toptracks':
            items = top_tracks(artistid)
        elif info == 'similar':
            items = similar_artists(artistid)
    xbmcplugin.setContent(handle, 'artists' if info == 'similar' else 'songs')
    xbmcplugin.addDirectoryItems(handle, items, len(items))
    xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)


if __name__ == '__main__':
    main()
