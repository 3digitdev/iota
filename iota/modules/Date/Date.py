import datetime

from modules.Module import Module


class Date(Module):
    def __init__(self, pipe):
        super().__init__(self, pipe)

    def run(self, command: str, regex) -> str:
        try:
            now = datetime.datetime.now()
            day = self._parse_day(now)
            self.say('It is {0:%A} {0:%B} {1}, {0:%Y}'.format(now, day))
        except Exception as e:
            self.log_exception(e)

    def _parse_day(self, now: datetime.date) -> str:
        day = f'{now:%d}'.lstrip('0')
        if day.endswith('1'):
            day = f'{day}st'
        elif day.endswith('2'):
            day = f'{day}nd'
        elif day.endswith('3'):
            day = f'{day}rd'
        else:
            day = f'{day}th'
        return day
