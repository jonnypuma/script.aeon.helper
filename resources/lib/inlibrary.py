# -*- coding: utf-8 -*-
"""Which Planner entries are in the library already (0.3.58): an upcoming episode that is already there (it aired today
and was fetched), a film out in cinemas that is already in the library, an album that is already there.

No Kodi imports: the JSON-RPC call is passed in (rpc(method, params) -> result dict), so this is tested without Kodi.
One Lookup per list: each show's episodes, each title's films and each album title are asked once."""


def _norm(text):
    return ' '.join((text or '').lower().replace('&', 'and').split())


class Lookup(object):
    def __init__(self, rpc):
        self.rpc = rpc
        self._shows = None          # normalised title -> [tvshowid], asked per title
        self._episodes = {}         # (tvshowid, season) -> set((season, episode)) that have a file
        self._films = {}            # normalised title -> [years]
        self._albums = {}           # normalised title -> [normalised artists]
        self._prefetched = None     # prefetch(): episodes found, films found, shows and titles asked

    def _call(self, method, params):
        try:
            return self.rpc(method, params) or {}
        except Exception:
            return {}

    def show_ids(self, title):
        """Library ids of the shows called so (asked per title: a list of the whole library was slow on the box)."""
        name = _norm(title)
        if not name:
            return []
        if self._shows is None:
            self._shows = {}
        if name not in self._shows:
            found = self._call('VideoLibrary.GetTVShows', {'properties': ['title'],
                                                            'filter': {'field': 'title', 'operator': 'is', 'value': title}}).get('tvshows') or []
            self._shows[name] = [show.get('tvshowid') for show in found if _norm(show.get('title') or show.get('label')) == name]
        return self._shows[name]

    def episodes(self, tvshowid, season):
        """(season, episode) pairs with a file, asked per show and season (a long show's whole list was slow)."""
        key = (tvshowid, season)
        if key not in self._episodes:
            found = self._call('VideoLibrary.GetEpisodes', {'tvshowid': tvshowid, 'season': season,
                                                             'properties': ['season', 'episode', 'file']}).get('episodes') or []
            self._episodes[key] = set((int(e.get('season') or 0), int(e.get('episode') or 0)) for e in found if e.get('file'))
        return self._episodes[key]

    def episode(self, showtitle, season, episode):
        try:
            key = (int(season or 0), int(episode or 0))
        except (TypeError, ValueError):
            return False
        if key == (0, 0):
            return False
        for tvshowid in self.show_ids(showtitle):
            if tvshowid is not None and key in self.episodes(tvshowid, key[0]):
                return True
        return False

    def film(self, title, year=None):
        name = _norm(title)
        if not name:
            return False
        if name not in self._films:
            found = self._call('VideoLibrary.GetMovies', {'properties': ['year', 'file'],
                                                           'filter': {'field': 'title', 'operator': 'is', 'value': title}}).get('movies') or []
            self._films[name] = [int(m.get('year') or 0) for m in found if m.get('file')]
        years = self._films[name]
        if not years:
            return False
        if not year:
            return True
        try:
            year = int(year)
        except (TypeError, ValueError):
            return True
        # a film's year in the library and in a release calendar can be a year apart (festival vs. release)
        return any(not y or abs(y - year) <= 1 for y in years)

    def album(self, title, artist=''):
        name = _norm(title)
        if not name:
            return False
        if name not in self._albums:
            found = self._call('AudioLibrary.GetAlbums', {'properties': ['artist'],
                                                          'filter': {'field': 'album', 'operator': 'is', 'value': title}}).get('albums') or []
            self._albums[name] = [_norm(' '.join(a.get('artist') or [])) for a in found]
        artists = self._albums[name]
        if not artists:
            return False
        return not artist or any(_norm(artist) in a or a in _norm(artist) for a in artists)

    def prefetch(self, entries):
        """Ask for all entries of a list at once: one episode query and one film query with an 'or' of every entry
        (each JSON-RPC call cost about 0.1 s on the box; one call per show and film made a day list 2 s slower).
        Afterwards has() answers from what came back; anything not asked here is still asked one by one."""
        if self._prefetched is None:
            self._prefetched = {'episodes': set(), 'films': {}, 'shows': set(), 'titles': set()}
        wanted = []
        films = []
        for entry in entries or ():
            kind = entry.get('kind') or 'episode'
            if kind == 'movie' and entry.get('title'):
                films.append(entry['title'])
            elif kind == 'episode' and entry.get('showtitle'):
                try:
                    season, number = int(entry.get('season') or 0), int(entry.get('episode') or 0)
                except (TypeError, ValueError):
                    continue
                if season or number:
                    wanted.append((entry['showtitle'], season, number))
        if wanted:
            rules = [{'and': [{'field': 'tvshow', 'operator': 'is', 'value': show},
                              {'field': 'season', 'operator': 'is', 'value': str(season)},
                              {'field': 'episode', 'operator': 'is', 'value': str(number)}]} for show, season, number in wanted]
            found = self._call('VideoLibrary.GetEpisodes', {'properties': ['showtitle', 'season', 'episode', 'file'],
                                                             'filter': {'or': rules}}).get('episodes') or []
            for e in found:
                if e.get('file'):
                    self._prefetched['episodes'].add((_norm(e.get('showtitle')), int(e.get('season') or 0), int(e.get('episode') or 0)))
            self._prefetched['shows'].update(_norm(show) for show, _s, _e in wanted)
        if films:
            rules = [{'field': 'title', 'operator': 'is', 'value': title} for title in films]
            found = self._call('VideoLibrary.GetMovies', {'properties': ['title', 'year', 'file'], 'filter': {'or': rules}}).get('movies') or []
            for m in found:
                if m.get('file'):
                    self._prefetched['films'].setdefault(_norm(m.get('title') or m.get('label')), []).append(int(m.get('year') or 0))
            for title in films:
                self._films.setdefault(_norm(title), self._prefetched['films'].get(_norm(title), []))

    def has(self, entry):
        """True when the entry (a Planner entry dict) is in the library already."""
        kind = entry.get('kind') or 'episode'
        if kind == 'movie':
            premiered = entry.get('premiered') or ''
            return self.film(entry.get('title'), entry.get('year') or (premiered[:4] if premiered[:4].isdigit() else None))
        if kind == 'album':
            return self.album(entry.get('title'), entry.get('artist') or '')
        if self._prefetched is not None and _norm(entry.get('showtitle')) in self._prefetched['shows']:
            try:
                key = (_norm(entry.get('showtitle')), int(entry.get('season') or 0), int(entry.get('episode') or 0))
            except (TypeError, ValueError):
                return False
            return key in self._prefetched['episodes']
        return self.episode(entry.get('showtitle'), entry.get('season'), entry.get('episode'))
