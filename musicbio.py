# -*- coding: utf-8 -*-
"""Album or artist bio where Kodi gives the skin none (skin 0.56.11; the user: "Album or artist bio").

An album row has the album's review (Album_Description) but not its artist's bio, and a song row has neither. While the
music window shows albums or songs, the service publishes for the item in focus / the album being listed:
    aeon.m.bio          the text
    aeon.m.bio.album    the album (DBID) it belongs to, for album rows: the artist's bio when the album has no review
    aeon.m.bio.path     the folder it belongs to, for a song list: the album's review, else the artist's bio
The skin's Aeon_M_Bio shows it only while it matches what is on screen. Looked up once per album and kept."""
import json
import re

import xbmc
import xbmcgui


def rpc(method, params):
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return json.loads(xbmc.executeJSONRPC(request)).get('result') or {}


def album_of(path):
    """the album id of a song list's folder (musicdb://albums/165/, musicdb://artists/12/165/ ...) or None"""
    numbers = re.findall(r'/(\d+)(?=/)', path or '')
    if '/albums/' in (path or '') and numbers:
        found = re.search(r'/albums/(\d+)/', path)
        if found:
            return int(found.group(1))
    return int(numbers[-1]) if numbers else None


class MusicBio(object):
    def __init__(self):
        self.key = None
        self.cache = {}

    def set(self, text, album='', path=''):
        home = xbmcgui.Window(10000)
        for name, value in (('aeon.m.bio', text), ('aeon.m.bio.album', album), ('aeon.m.bio.path', path)):
            if home.getProperty(name) != value:
                home.setProperty(name, value)

    def text(self, albumid, album_first):
        key = (albumid, album_first)
        if key not in self.cache:
            found = ''
            details = rpc('AudioLibrary.GetAlbumDetails', {'albumid': albumid, 'properties': ['description', 'artistid']}).get('albumdetails') or {}
            if album_first and (details.get('description') or '').strip():
                found = details['description'].strip()
            else:
                for artistid in details.get('artistid') or []:
                    artist = rpc('AudioLibrary.GetArtistDetails', {'artistid': artistid, 'properties': ['description']}).get('artistdetails') or {}
                    if (artist.get('description') or '').strip():
                        found = artist['description'].strip()
                        break
            if len(self.cache) > 2000:
                self.cache.clear()
            self.cache[key] = found
        return self.cache[key]

    def tick(self):
        try:
            if not xbmc.getCondVisibility('Window.IsActive(music)'):
                if self.key is not None:
                    self.key = None
                    self.set('')
                return
            if xbmc.getCondVisibility('Container.Content(albums)'):
                dbid = xbmc.getInfoLabel('ListItem.DBID')
                key = ('album', dbid)
                if key == self.key:
                    return
                self.key = key
                if not dbid.isdigit() or xbmc.getInfoLabel('ListItem.Property(Album_Description)'):
                    self.set('')                    # the album has its own review: the skin shows that
                    return
                self.set(self.text(int(dbid), False), album=dbid)
            elif xbmc.getCondVisibility('Container.Content(songs)'):
                path = xbmc.getInfoLabel('Container.FolderPath')
                key = ('songs', path)
                if key == self.key:
                    return
                self.key = key
                albumid = album_of(path)
                self.set(self.text(albumid, True) if albumid else '', path=path if albumid else '')
            elif self.key is not None:
                self.key = None
                self.set('')
        except Exception as error:                  # never stop the service over this
            xbmc.log('[script.aeon.helper] music bio: %s' % error, xbmc.LOGINFO)
