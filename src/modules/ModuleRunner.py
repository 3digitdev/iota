import json
import os

from modules.Module import ModuleError


class ModuleRunner(object):
    __slots__ = ['cmd_map', 'all_commands']

    def __init__(self):
        self.cmd_map = {}
        self.all_commands = []
        for class_name in os.listdir("modules"):
            if class_name == "__pycache__":
                continue
            if os.path.isdir(os.path.join("modules", class_name)):
                filename = f"{class_name.lower()}.json"
                path = os.path.join("modules", class_name, filename)
                with open(path, "r") as cfg:
                    config = json.load(cfg)
                if "command_words" not in config.keys():
                    raise ModuleError(
                        class_name,
                        "Improperly formatted config: No command words"
                    )
                self.cmd_map[class_name] = config["command_words"]
                self.all_commands.extend(config["command_words"])

    def run_module(self, command):
        if command not in self.all_commands:
            return None
        for name, cmds in self.cmd_map.items():
            if command in cmds:
                try:
                    exec(f"from modules.{name}.{name} import {name}")
                    module = eval(f"{name}()")
                    module.run(command)
                except ModuleError:
                    raise
                break
