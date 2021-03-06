import os
import re
from word2number import w2n

from modules.Module import Module
from modules.GoogleMusic.GoogleMusicController import GoogleMusicController
from utils.mod_utils import get_params


class GoogleMusic(Module):
    def __init__(self, pipe):
        super().__init__(self, pipe)
        self.gmusic = GoogleMusicController()
        self.current_volume = 0
        self.set_volume(5)

    def run(self, command: str, regex: str) -> str:
        try:
            params = get_params(command, regex, self.regexes.keys())
            self._pick_action(command, params)
            self.await_next_command()
        except Exception as e:
            self.log_exception(e)

    def _pick_action(self, command: str, params: dict) -> str:
        result = None
        # Volume
        if params['volume'] == 'up':
            return self.volume_up()
        elif params['volume'] == 'down':
            return self.volume_down()
        elif params['volume'] != '':
            return self.set_volume(w2n.word_to_num(params['volume']))
        # Song Control
        if command.startswith('pause'):
            return self.gmusic.pause_song()
        if command.startswith('stop'):
            self.finish_action()
            return self.gmusic.stop_player()
        if params['direction'] == 'next':
            return self.gmusic.next_song()
        if params['direction'] == 'previous':
            return self.gmusic.previous_song()
        if command.startswith('start') and command.endswith('over'):
            return self.gmusic.start_over('song' not in command)
        # Playing songs
        if command.startswith('resume'):
            return self.gmusic.resume_song()
        if re.match(r'play ?(?:music|song)?$', command):
            return self.gmusic.resume_song()
        if params['playlist'] != '':
            result = self.gmusic.play_playlist(
                params['playlist'],
                lambda: self.finish_action,
                shuffle=command.startswith('shuffle'),
            )
        elif params['song'] != '':
            result = self.gmusic.play_song(
                params['song'],
                lambda: self.finish_action,
                params['artist'],
                params['album']
            )
        if result is not None:
            self.say(result)

    def set_volume(self, volume: int):
        volume = max(0, min(volume, 10))
        self.current_volume = volume
        # Only works in Linux/Unix!
        os.system(f'amixer sset "Master" {volume}0%')

    def volume_up(self):
        self.set_volume(self.current_volume + 1)

    def volume_down(self):
        self.set_volume(self.current_volume - 1)

    def pause_if_running(self):
        self.gmusic.pause_song()

    def resume_if_running(self):
        self.gmusic.resume_song()
