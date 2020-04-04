import os
import re
from word2number import w2n
import json

from modules.Module import BackgroundModule, ModuleError
from modules.GoogleMusic.GoogleMusicController import GoogleMusicController
from utils.mod_utils import get_params


class GoogleMusic(BackgroundModule):
    def __init__(self):
        super().__init__(self)
        print("INITIALIZING GOOGLE MUSIC MODULE")
        self.gmusic = GoogleMusicController()
        self.current_volume = 0
        self.set_volume(5)

    def run(self, command: str, regex: str) -> str:
        params = get_params(command, regex, self.regexes.keys())
        return self._pick_action(command, params)

    def _pick_action(self, command: str, params: dict) -> str:
        result = ""
        # Volume
        if params["volume"] == "up":
            return self.volume_up()
        elif params["volume"] == "down":
            return self.volume_down()
        elif params["volume"] != "":
            return self.set_volume(w2n.word_to_num(params["volume"]))
        # Song Control
        if command.startswith("pause"):
            return self.gmusic.pause_song()
        if command.startswith("stop"):
            return self.gmusic.stop_player()
        if params["direction"] == "next":
            return self.gmusic.next_song()
        if params["direction"] == "previous":
            return self.gmusic.previous_song()
        if command.startswith("start") and command.endswith("over"):
            return self.gmusic.start_over("song" not in command)
        # Playing songs
        if re.match(r'play ?(?:music|song)?$', command):
            return self.gmusic.resume_song()
        if params["playlist"] != "":
            if self.callback_at_end is None:
                raise ModuleError("GoogleMusic", "You didn't set the callback")
            result = self.gmusic.play_playlist(
                params["playlist"],
                self.callback_at_end,
                shuffle=command.startswith("shuffle"),
            )
            if result is not None:
                return result
        if params["song"] != "":
            if self.callback_at_end is None:
                raise ModuleError("GoogleMusic", "You didn't set the callback")
            result = self.gmusic.play_song(
                params["song"],
                self.callback_at_end,
                params["artist"],
                params["album"]
            )
            if result is not None:
                return result
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
