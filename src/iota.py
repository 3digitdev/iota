import json
from Speech2Text import Speech2Text, RecognizerSource


class Iota(object):
    __slots__ = ['s2t', 'wake_words']

    def __init__(self):
        self._read_config()
        self.s2t = Speech2Text(
            RecognizerSource.GOOGLE, self.wake_words, filter=True
        )

    def _read_config(self):
        with open("config.json", "r") as cfg:
            config = json.load(cfg)
        self.wake_words = config['wake_words']

    def listen(self):
        self.s2t.active_listen()


def main():
    import speech_recognition as sr
    print(sr.__version__)
    iota = Iota()
    iota.listen()


if __name__ == "__main__":
    main()
