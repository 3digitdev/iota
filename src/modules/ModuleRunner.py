import json
import os

from modules.Time import Time


class ModuleRunner(object):
    __slots__ = ['cmd_map', 'all_commands']

    def __init__(self):
        print(os.getcwd())
        self.cmd_map = {}
        self.all_commands = []
        for filename in os.listdir("modules/configs"):
            class_name = filename.split(".")[0].capitalize()
            with open(os.path.join("modules/configs", filename), "r") as cfg:
                config = json.load(cfg)
                self.cmd_map[class_name] = config["command_words"]
                self.all_commands.extend(config["command_words"])

    def run_module(self, command):
        if command not in self.all_commands:
            return None
        for name, cmds in self.cmd_map.items():
            if command in cmds:
                module = eval(f"{name}()")
                module.run(command)
                break
