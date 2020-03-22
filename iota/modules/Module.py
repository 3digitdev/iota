import json
import os


class ModuleError(Exception):
    def __init__(self, module, message, inner=""):
        self.module = module
        self.message = message
        if inner != "":
            self.message += f"\n    {inner}"


class Module(object):
    __slots__ = ['commands']

    def __init__(self, child):
        module = child.__class__.__name__
        path = os.path.join("iota", "modules", module)
        with open(os.path.join(path, f"{module.lower()}.json"), "r") as mcfg:
            config = json.load(mcfg)
        if "command_words" not in config.keys():
            raise ModuleError(
                module,
                "Improperly formatted config: No command words"
            )
        child.commands = config["command_words"]

    def run(self, command: str):
        pass
