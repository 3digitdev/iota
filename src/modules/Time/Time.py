import datetime

from modules.Module import Module


class Time(Module):
    def __init__(self):
        super().__init__(self)

    def run(self, command: str):
        now = datetime.datetime.now()
        print("It is {0:%I}:{0:%M}:{0:%S} {0:%p}".format(now))
