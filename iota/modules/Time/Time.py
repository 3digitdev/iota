import datetime
import re
from word2number import w2n
from multiprocessing import Process, Event, Manager

from modules.Module import Module
from utils.mod_utils import get_params


class Timer(Process):
    def __init__(self, interval: int, callback):
        super(Timer, self).__init__()
        self.interval = interval
        self.callback = callback
        self.finished = Event()

    def cancel(self):
        self.finished.set()

    def run(self):
        self.finished.wait(self.interval)
        if not self.finished.is_set():
            self.callback('alarm_chime.mp3')
        self.finished.set()


class Time(Module):
    def __init__(self):
        super().__init__(self)
        self.timer = None
        self.timer_data = Manager().dict()

    def run(self, command: str, regex) -> str:
        params = get_params(command, regex, self.regexes.keys())
        if all([v == '' for v in params.values()]):
            if 'stop' in command or 'cancel' in command:
                if self.timer is not None:
                    self.timer.cancel()
                    return self.say('Timer has been cancelled')
                else:
                    return self.say('No timer has been set')
            now = datetime.datetime.now()
            self.say('It is {0:%I}:{0:%M} {0:%p}'.format(now))
            return
        if any([v == '' for v in [params['duration'], params['increment']]]):
            # They forgot one or both of the parameters
            return
        if self.timer is not None:
            return self.say('You already have a timer set')
        seconds = self._complex_to_seconds(params)
        self._spawn_timer(seconds)
        self.say('Timer set')

    def _complex_to_seconds(self, params) -> int:
        primary = {
            'duration': params['duration'],
            'increment': params['increment'],
            'mod': params['increment_mod']
        }
        primary_is_complex = primary['mod'] != ''
        p_duration = self._duration_to_num(primary['duration'])
        if primary['mod'] == 'half':
            p_duration *= 1.5
        elif primary['mod'] == 'quarter':
            p_duration *= 1.25

        seconds = self._to_seconds(p_duration, primary['increment'])
        if primary_is_complex:
            return seconds
        secondary = {
            'duration': params['duration2'], 'increment': params['increment2']
        }
        tertiary = {
            'duration': params['duration3'], 'increment': params['increment3']
        }
        for param_set in [secondary, tertiary]:
            if None in param_set.values():
                break
            duration = self._duration_to_num(param_set['duration'])
            seconds += self._to_seconds(duration, param_set['increment'])
        return seconds

    def _duration_to_num(self, duration: str) -> int:
        if re.match(r'an?', duration):
            duration = 'one'
        return w2n.word_to_num(duration)

    def _to_seconds(self, duration: float, increment: str) -> int:
        result = {
            'second': lambda d: d,
            'minute': lambda d: d * 60,
            'hour': lambda d: d * 60 * 60,
            'day': lambda d: d * 60 * 60 * 24
        }[increment](duration)
        # subtract 1 from the total because the TTS call takes a second
        return int(round(result)) - 1

    def _spawn_timer(self, seconds: int) -> None:
        self.timer = Timer(seconds, callback=self.play_mp3)
        self.timer.start()
