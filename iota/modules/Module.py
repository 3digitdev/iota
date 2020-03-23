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
        # Get the name of the module for later
        module = child.__class__.__name__
        path = os.path.join("iota", "modules", module)
        # Load that module's config
        with open(os.path.join(path, f"{module.lower()}.json"), "r") as mcfg:
            config = json.load(mcfg)
        # Verify the config file has at least commands
        if "command_words" not in config.keys():
            raise ModuleError(
                module,
                "Improperly formatted config: No command words"
            )
        # assign the regex-built commands to the Module
        child.commands = Utils.parse_to_regexes(config)
        if "regexes" in config.keys():
            # Also assign the unprocessed regexes from config if needed
            child.regexes = config["regexes"]

    def run(self, command: str, regex):
        pass
