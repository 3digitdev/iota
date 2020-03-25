import json
import os
import re
from gtts import gTTS

from modules.Module import ModuleError
import utils.mod_utils as Utils


class ModuleRunner(object):
    __slots__ = ['cmd_map', 'all_commands']

    def __init__(self):
        # maps each module name to a list of its regexed commands
        self.cmd_map = {}
        # all valid commands for Iota, for quick lookup
        self.all_commands = []
        for class_name in os.listdir(os.path.join("iota", "modules")):
            if class_name == "__pycache__":
                continue
            # open each module folder in turn
            if os.path.isdir(os.path.join("iota", "modules", class_name)):
                self._load_module(class_name)

    def _load_module(self, class_name: str):
        # Load the module and its commands into memory
        cfg_file = f"{class_name.lower()}.json"
        cfg_path = os.path.join(
            "iota", "modules", class_name, cfg_file
        )
        try:
            with open(cfg_path, "r") as cfg:
                config = json.load(cfg)
            # quick schema check
            if "command_words" not in config.keys():
                raise ModuleError(
                    class_name,
                    "Improperly formatted config: No command words"
                )
            # store the processed regexes here as well for quick lookup
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
            # The command doesn't match any valid commands Iota knows
            return None
        # We matched something, let's do the thing
        for name, cmds in self.cmd_map.items():
            for regex in cmds:
                if re.match(regex, command):
                    # We found the Module/command that matches
                    found = True
                    print(f"    MATCHED for {name}:")
                    print(f"      {regex}")
                    try:
                        # Dynamically import the Module
                        exec(f"from modules.{name}.{name} import {name}")
                        # Instantiate the Module
                        module = eval(f"{name}()")
                        response = module.run(command, regex)
                        # Modules that talk back should return the response str
                        if response is not None and response != "":
                            print(f"RESPONSE:  {response}")
                            self._say(response)
                    except ModuleError:
                        raise
                    break
            if found:
                break

    def _say(self, phrase):
        tts = gTTS(text=phrase, lang='en', slow=False)
        # We store the command for 2 reasons:
        #  1. gTTS doesn't ACTUALLY utilize the speaker.
        #  2. We can re-use this last command in Modules like RepeatPhrase
        tts.save('last_command.mp3')
        os.system('mpg123 --quiet last_command.mp3')
