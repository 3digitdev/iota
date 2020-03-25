import time
import signal
import subprocess
import os
import psutil
from multiprocessing import Process, Manager
from gmusicapi import Mobileclient


"""
Reference:
https://unofficial-google-music-api.readthedocs.io/en/latest/reference/mobileclient.html
"""


class Song(object):
    def __init__(self, song_data: dict):
        self.id = song_data["storeId"]
        self.name = song_data["title"]
        self.artist = song_data["artist"]
        if song_data["album"] == "<|\u00ba_\u00ba|>":
            song_data["album"] = "Robot Face"
        self.album = song_data["album"]


class Artist(object):
    def __init__(self, artist_data: dict):
        self.id = artist_data["artistId"]
        self.name = artist_data["name"]


class Album(object):
    def __init__(self, album_data: dict):
        self.id = album_data["albumId"]
        self.name = album_data["name"]
        self.artist = album_data["artist"]


class Playlist(object):
    def __init__(self, name):
        self.name = name
        self.songs = []

    def add_song(self, song_data):
        self.songs.append(Song(song_data))

    def set_list(self, song_list: list):
        self.songs = song_list

    def __len__(self):
        return len(self.songs)


class SearchResults(object):
    def __init__(self, raw_data):
        self.songs = []
        for s in raw_data["song_hits"]:
            self.songs.append(Song(s["track"]))
        self.artists = []
        for a in raw_data["artist_hits"]:
            self.artists.append(Artist(a["artist"]))
        self.albums = []
        for a in raw_data["album_hits"]:
            self.albums.append(Album(a["album"]))


class GoogleMusicController(object):
    def __init__(self):
        self.device_id = os.environ["GOOGLE_MUSIC_DEVICE_ID"]
        self.client = Mobileclient()
        # TODO: change this to relative path from run location
        self.client.oauth_login(Mobileclient.FROM_MAC_ADDRESS, "auth.json")
        self.process = None
        self.player = None
        self.playlist = Playlist("IotaGoogleMusicController")
        self.current_index = -1

    def get_playlist(self, name: str) -> Playlist:
        playlists = self.client.get_all_user_playlist_contents()
        matched_playlists = [p for p in playlists if name in p["name"].lower()]
        if len(matched_playlists) > 0:
            found = matched_playlists[0]
            playlist = Playlist(found["name"])
            [playlist.add_song(track["track"]) for track in found["tracks"]]
            return playlist
        return None

    def play_songs(self, songs: list):
        self.playlist.set_list(songs)
        self.current_index = 0
        self._play_current_song()
        return

    def _play_current_song(self):
        if len(self.playlist) == 0:
            return
        if 0 <= self.current_index < len(self.playlist):
            current_song = self.playlist.songs[self.current_index]
            self._spawn_player(current_song.id)
        return

    def next_song(self) -> str:
        if len(self.playlist) == 0:
            return "no playlist"
        if self.current_index == len(self.playlist) - 1:
            return "end of playlist"
        self.current_index += 1
        self._play_current_song()
        return ""

    def previous_song(self) -> str:
        if len(self.playlist) == 0:
            return "no playlist"
        if self.current_index == 0:
            return "start of playlist"
        self.current_index -= 1
        self._play_current_song()
        return ""

    def start_over(self, playlist: bool = False):
        if playlist:
            self.current_index = 0
        if len(self.playlist) == 0:
            return "no playlist"
        if 0 <= self.current_index < len(self.playlist):
            self.current_index = 0
        self._play_current_song()
        return ""

    def get_song(self, name: str, artist: str = "", album: str = "") -> Song:
        if artist != "" and album != "":
            return self._get_entity(
                name,
                "songs",
                lambda x: x.artist == artist and x.album == album
            )
        if artist != "":
            return self._get_entity(
                name, "songs", lambda x: x.artist == artist
            )
        if album != "":
            return self._get_entity(
                name, "songs", lambda x: x.album == album
            )
        return self._get_entity(name, "songs")

    def get_album(self, name: str, artist: str = "") -> Album:
        if artist != "":
            return self._get_entity(
                name, "albums", lambda x: x.artist == artist
            )
        return self._get_entity(name, "albums")

    def get_artist(self, name: str) -> Artist:
        return self._get_entity(name, "artists")

    def _get_entity(self, name: str, type: str, extra_filter=lambda _: True):
        results = self.search(name).__dict__[type]
        if len(results) == 0:
            return None
        results = list(filter(extra_filter, results))
        # We will trust Google's ability to filter search results... :P
        return results[0]

    def _run_multiprocess(self, on_exit, command, share):
        process = subprocess.Popen(command)
        share["pid"] = process.pid
        process.wait()
        on_exit()
        return

    def _spawn_player(self, track_id: str):
        stream_url = self.client.get_stream_url(
            track_id, device_id=self.device_id
        ).replace('https', 'http')
        self.stop_song()
        self.manager = Manager()
        self.shared_vars = self.manager.dict()
        self.player = Process(
            target=self._run_multiprocess,
            args=(
                self.next_song,
                ['mpg123', '--quiet', stream_url],
                self.shared_vars
            )
        )
        self.player.start()

    def pause_song(self):
        if "pid" in self.shared_vars.keys():
            psutil.Process(self.shared_vars["pid"]).send_signal(signal.SIGSTOP)

    def resume_song(self):
        if "pid" in self.shared_vars.keys():
            psutil.Process(self.shared_vars["pid"]).send_signal(signal.SIGCONT)

    def stop_song(self):
        if self.player is not None:
            if "pid" in self.shared_vars.keys():
                psutil.Process(self.shared_vars["pid"]) \
                      .send_signal(signal.SIGTERM)
                self.shared_vars = None
                self.manager = None
            self.player.terminate()
            self.player = None

    def search(self, query: str, max_results: int = 100) -> SearchResults:
        results = self.client.search(query, max_results)
        return SearchResults(results)


def main():
    gmusic = GoogleMusicController()
    # print(gmusic.get_song("I'm Good", "GRiZ"))
    playlist = gmusic.get_playlist("funkstep")
    # print(playlist.songs[0].artist)
    gmusic.play_songs(playlist.songs)
    time.sleep(3)
    gmusic.pause_song()
    time.sleep(3)
    gmusic.resume_song()
    gmusic.stop_song()
    # print(gmusic.process)


if __name__ == "__main__":
    main()
