import json
import os
import re
from gtts import gTTS

from modules.Module import ModuleError
import utils.mod_utils as Utils


class ModuleRunner(object):
    __slots__ = ['cmd_map', 'all_commands']

    def __init__(self):
        self.cmd_map = {}
        self.all_commands = []
        for class_name in os.listdir(os.path.join("iota", "modules")):
            if class_name == "__pycache__":
                continue
            if os.path.isdir(os.path.join("iota", "modules", class_name)):
                filename = f"{class_name.lower()}.json"
                path = os.path.join("iota", "modules", class_name, filename)
                try:
                    with open(path, "r") as cfg:
                        config = json.load(cfg)
                    if "command_words" not in config.keys():
                        raise ModuleError(
                            class_name,
                            "Improperly formatted config: No command words"
                        )
                    command_regexes = Utils.parse_to_regexes(config)
                    self.cmd_map[class_name] = command_regexes
                    self.all_commands.extend(command_regexes)
                except json.JSONDecodeError as err:
                    raise ModuleError(
                        class_name,
                        f"Improperly formatted config: Invalid JSON",
                        inner=f"{err.msg} (Line {err.lineno})"
                    )

    def run_module(self, command):
        found = False
        if not any([re.match(reg, command) for reg in self.all_commands]):
            return None
        for name, cmds in self.cmd_map.items():
            for regex in cmds:
                if re.match(regex, command):
                    found = True
                    print(f"    MATCHED for {name}:")
                    print(f"      {regex}")
                    try:
                        exec(f"from modules.{name}.{name} import {name}")
                        module = eval(f"{name}()")
                        response = module.run(command, regex)
                        if response is not None and response != "":
                            self._say(response)
                    except ModuleError:
                        raise
                    break
            if found:
                break

    def _say(self, phrase):
        tts = gTTS(text=phrase, lang='en', slow=False)
        tts.save('last_command.mp3')
        os.system('mpg123 last_command.mp3')
