import json


class Module(object):
    __slots__ = ['commands']

    def __init__(self, child):
        module = child.__class__.__name__
        with open(f"modules/{module}/{module.lower()}.json", "r") as mcfg:
            config = json.load(mcfg)
        child.commands = config["command_words"]

    def run(self, command: str):
        pass
