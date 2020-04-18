import datetime
from word2number import w2n
from multiprocessing import Process, Event, Manager

from modules.Module import BackgroundModule
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


class Time(BackgroundModule):
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
                    return self.callback_at_end('Timer has been cancelled')
                else:
                    return self.callback_at_end('No timer has been set')
            now = datetime.datetime.now()
            return self.callback_at_end(
                'It is {0:%I}:{0:%M} {0:%p}'.format(now)
            )
        duration = params['duration']
        increment = params['increment']
        if any([v == '' for v in [duration, increment]]):
            # They forgot one or both of the parameters
            return self.callback_at_end('')
        if self.timer is not None:
            return self.callback_at_end('You already have a timer set')
        seconds = self._to_seconds(w2n.word_to_num(duration), increment)
        self._spawn_timer(seconds)

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
        self.timer = Timer(seconds, callback=self.callback_at_end)
        self.timer.start()
