#!/usr/bin/env python3
import json
import os

from Speech2Text import Speech2Text, RecognizerSource
from modules.Module import ModuleError


class Iota(object):
    __slots__ = ['s2t', 'wake_words']

    def __init__(self):
        self._read_config()
        try:
            self.s2t = Speech2Text(
                RecognizerSource.GOOGLE, self.wake_words, filter=True
            )
        except ModuleError:
            raise

    def _read_config(self):
        with open(os.path.join("iota", "config.json"), "r") as cfg:
            config = json.load(cfg)
        self.wake_words = config['wake_words']

    def listen(self):
        try:
            self.s2t.active_listen()
        except ModuleError:
            raise


def main():
    try:
        iota = Iota()
        iota.listen()
    except ModuleError as err:
        print(f"Your {err.module} module has an error:\n  {err.message}")


if __name__ == "__main__":
    main()
