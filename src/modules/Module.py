import json


class Module(object):
    __slots__ = ['commands']

    def __init__(self, child):
        module_name = child.__class__.__name__.lower()
        with open(f"modules/configs/{module_name}.json", "r") as mcfg:
            config = json.load(mcfg)
        child.commands = config["command_words"]

    def run(self, command: str):
        pass
