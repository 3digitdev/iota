import os
import re
from word2number import w2n
import random

from modules.Module import Module
from modules.GoogleMusic.GoogleMusicController import GoogleMusicController
from utils.mod_utils import get_params


class GoogleMusic(Module):
    def __init__(self):
        super().__init__(self)
        self.gmusic = GoogleMusicController()
        self.current_volume = 0
        self.set_volume(5)

    def run(self, command: str, regex) -> str:
        params = get_params(command, regex, self.regexes.keys())
        return self._pick_action(command, params)

    def _pick_action(self, command: str, params: dict) -> str:
        result = ""
        # Easy ones first
        if params["volume"] == "up":
            return self.volume_up()
        elif params["volume"] == "down":
            return self.volume_down()
        else:
            return self.set_volume(w2n.word_to_num(params["volume"]))
        if command.startswith("pause"):
            return self.gmusic.pause_song()
        if command.startswith("stop"):
            return self.gmusic.stop_song()
        if re.match(r'play ?(?:music|song)?$'):
            return self.gmusic.resume_song()
        if params["direction"] == "next":
            return self.gmusic.next_song()
        if params["direction"] == "previous":
            return self.gmusic.previous_song()
        if command.startswith("start") and command.endswith("over"):
            return self.gmusic.start_over("song" not in command)
        if params["playlist"] != "":
            songs = self.gmusic.get_playlist(params["playlist"]).songs
            if command.startswith("shuffle"):
                random.shuffle(songs)
            return self.gmusic.play_songs(songs)
        if params["song"] != "":
            song = self.gmusic.get_song(
                params["song"], params["artist"], params["album"]
            )
            return self.gmusic.play_songs([song])
        # Disabled because gmusicapi doesn't return album songlists
        # elif params["album"] != "":
        #     album = self.gmusic.get_album(params["album"], params["artist"])
        # Disabled because gmusicapi doesn't return the artist albums
        # elif params["artist"] != "":
        #     artist = self.gmusic.get_artist(params["artist"])
        return result

    def set_volume(self, volume: int):
        volume = max(0, min(volume, 10))
        self.current_volume = volume
        # Only works in Linux/Unix!
        os.system(f"amixer sset 'Master' {volume}0%")

    def volume_up(self):
        self.set_volume(self.current_volume + 1)

    def volume_down(self):
        self.set_volume(self.current_volume - 1)
