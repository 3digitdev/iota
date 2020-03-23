import json
import os

import utils.mod_utils as Utils


class ModuleError(Exception):
    def __init__(self, module, message, inner=""):
        self.module = module
        self.message = message
        if inner != "":
            self.message += f"\n    {inner}"


class Module(object):
    __slots__ = ['commands', 'regexes']

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
        child.commands = Utils.parse_to_regexes(config)
        if "regexes" in config.keys():
            child.regexes = config["regexes"]

    def run(self, command: str, regex):
        pass
