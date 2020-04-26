import signal
import random
import os
import psutil
from subprocess import Popen
from multiprocessing import Process, Manager
from gmusicapi import Mobileclient


'''
Reference:
https://unofficial-google-music-api.readthedocs.io/en/latest/reference/mobileclient.html
'''


class Song(object):
    def __init__(self, song_data: dict):
        self.id = song_data['storeId']
        self.name = song_data['title']
        self.artist = song_data['artist']
        if song_data['album'] == '<|\u00ba_\u00ba|>':
            song_data['album'] = 'Robot Face'
        self.album = song_data['album']


class Artist(object):
    def __init__(self, artist_data: dict):
        self.id = artist_data['artistId']
        self.name = artist_data['name']


class Album(object):
    def __init__(self, album_data: dict):
        self.id = album_data['albumId']
        self.name = album_data['name']
        self.artist = album_data['artist']


class Playlist(object):
    def __init__(self, name):
        self.name = name
        self.songs = []

    def add_song(self, song_data):
        self.songs.append(Song(song_data))

    def set_list(self, song_list: list):
        self.songs = song_list

    def shuffle(self):
        random.shuffle(self.songs)

    def __len__(self):
        return len(self.songs)


class SearchResults(object):
    def __init__(self, raw_data: dict):
        self.songs = []
        for s in raw_data['song_hits']:
            self.songs.append(Song(s['track']))
        self.artists = []
        for a in raw_data['artist_hits']:
            self.artists.append(Artist(a['artist']))
        self.albums = []
        for a in raw_data['album_hits']:
            self.albums.append(Album(a['album']))


class GoogleMusicController(object):
    def __init__(self):
        self.device_id = os.environ['GOOGLE_MUSIC_DEVICE_ID']
        self.client = Mobileclient(debug_logging=False)
        # TODO: change this to relative path from run location
        self.client.oauth_login(Mobileclient.FROM_MAC_ADDRESS, 'iota/auth.json')
        self.player_data = Manager().dict()
        self.player = None
        self.player_pid = None
        self.playlist = Playlist('Now Playing')

    def _get_entity(self, name: str, type: str, extra_filter=lambda _: True):
        results = self.search(name).__dict__[type]
        if len(results) == 0:
            return None
        results = list(filter(extra_filter, results))
        if len(results) == 0:
            return None
        # We will trust Google's ability to filter search results... :P
        return results[0]

    def _get_song(self, name: str, artist: str = '', album: str = '') -> Song:
        if artist != '' and album != '':
            return self._get_entity(
                name,
                'songs',
                lambda x:
                    x.artist.lower() == artist and x.album.lower() == album
            )
        if artist != '':
            return self._get_entity(
                name, 'songs', lambda x: x.artist.lower() == artist
            )
        if album != '':
            return self._get_entity(
                name, 'songs', lambda x: x.album.lower() == album
            )
        return self._get_entity(name, 'songs')

    def _get_album(self, name: str, artist: str = '') -> Album:
        if artist != '':
            return self._get_entity(
                name, 'albums', lambda x: x.artist == artist
            )
        return self._get_entity(name, 'albums')

    def _get_artist(self, name: str) -> Artist:
        return self._get_entity(name, 'artists')

    def _get_playlist(self, name: str) -> Playlist:
        playlists = self.client.get_all_user_playlist_contents()
        matched_playlists = []
        for p in playlists:
            p_name = p['name'].lower()
            if p_name == name or p_name == name.replace(' ', ''):
                matched_playlists.append(p)
        if len(matched_playlists) > 0:
            found = matched_playlists[0]
            self.playlist = Playlist(found['name'])
            [self.playlist.add_song(track['track'])
                for track in found['tracks']]
            return self.playlist
        return None

    def play_song(
        self, name: str, callback_at_end, artist: str = '', album: str = ''
    ):
        song = self._get_song(name, artist, album)
        if song is None:
            return f'I couldn\'t find a song called {name} by {artist}'
        return self.play_playlist(
            'Now Playing', callback_at_end, song_list=[song]
        )

    def play_playlist(
            self,
            name: str,
            callback_at_end,
            song_list=[],
            start=0,
            shuffle=False,
    ) -> str:
        if song_list == []:
            self.playlist = self._get_playlist(name)
            if self.playlist is None:
                return f'I couldn\'t find a playlist called {name}'
        else:
            self.playlist = Playlist(name)
            self.playlist.set_list(song_list)
        if shuffle:
            self.playlist.shuffle()

        # Embed this so we don't have to pass a bunch of context out
        def get_url(id):
            # we need to logout and log back in to allow rapid requesting
            # of stream_urls -- they expire after a minute, and can't be
            # re-requested before then without an SSLError...thanks Google.
            self.client.logout()
            self.client.oauth_login(Mobileclient.FROM_MAC_ADDRESS, 'auth.json')
            return self.client.get_stream_url(id, device_id=self.device_id)
        # Spawn a subprocess for the player
        self.player = Process(
            target=spawn_player,
            args=(
                get_url,
                self.playlist,
                self.player_data,
                callback_at_end,
                start
            )
        )
        self.player.start()
        self.player_pid = self.player.pid
        return None

    def pause_song(self):
        if 'pid' in self.player_data.keys():
            psutil.Process(self.player_data['pid']).send_signal(signal.SIGSTOP)

    def resume_song(self):
        if 'pid' in self.player_data.keys():
            psutil.Process(self.player_data['pid']).send_signal(signal.SIGCONT)

    def stop_player(self):
        if 'pid' in self.player_data.keys():
            psutil.Process(self.player_data['pid']).send_signal(signal.SIGSTOP)
        # self.player.terminate()

    def next_song(self) -> str:
        if 'pid' in self.player_data.keys():
            psutil.Process(self.player_data['pid']).send_signal(signal.SIGTERM)

    def previous_song(self) -> str:
        if 'index' not in self.player_data.keys():
            return 'Could not start the playlist, missing index'
        idx = self.player_data['index']
        idx = idx - 1 if idx > 0 else 0
        if not self.player_data['done']:
            self.stop_player()
        self.play_playlist(
            self.playlist.name.lower(), self.playlist.songs, start=idx
        )
        return ''

    def start_over(self):
        return ''

    def search(self, query: str, max_results: int = 100) -> SearchResults:
        results = self.client.search(query, max_results)
        return SearchResults(results)


def spawn_player(get_url, playlist, shared, callback_at_end, start=0):
    for index in range(start, len(playlist.songs)):
        song = playlist.songs[index]
        stream_url = get_url(song.id).replace('https', 'http')
        process = Popen(['mpg123', '--quiet', stream_url])
        shared['pid'] = process.pid
        shared['index'] = index
        shared['done'] = False
        process.wait()
    shared['done'] = True
    callback_at_end()
