import json


class ModuleError(Exception):
    def __init__(self, module, message):
        self.module = module
        self.message = message


class Module(object):
    __slots__ = ['commands']

    def __init__(self, child):
        module = child.__class__.__name__
        with open(f"modules/{module}/{module.lower()}.json", "r") as mcfg:
            config = json.load(mcfg)
        if "command_words" not in config.keys():
            raise ModuleError(
                module,
                "Improperly formatted config: No command words"
            )
        child.commands = config["command_words"]

    def run(self, command: str):
        pass
