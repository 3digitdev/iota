import json
import os
import re
import importlib
import psutil
import signal
from multiprocessing import Process, Manager
from subprocess import Popen
try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    print(
        "Importing the Speech SDK for Python failed."
        "Refer to"
        "https://docs.microsoft.com/azure/cognitive-services/speech-service/quickstart-python"
        "for installation instructions."
    )
    import sys
    sys.exit(1)

from modules.Module import BackgroundModule
import utils.mod_utils as Utils

AZURE_KEY = os.environ['AZURE_KEY']
AZURE_REGION = os.environ['AZURE_REGION']


class ModuleRunner(object):
    __slots__ = [
        'cmd_map', 'all_commands', 'speech_config',
        'speech_synthesizer', 'singletons', 'player', 'player_data'
    ]

    def __init__(self, speech_cfg):
        # maps each module name to a list of its regexed commands
        self.cmd_map = {}
        # all valid commands for Iota, for quick lookup
        self.all_commands = []
        # This is used for tracking running instances so we don't replicate
        # Also is helpful for Background Modules!
        self.singletons = {}
        # Playing mp3 stuff
        self.player = None
        self.player_data = Manager().dict()
        # Configure Azure Speech Synthesizer
        self.speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_KEY,
            region=AZURE_REGION
        )
        # Load all Modules
        for class_name in os.listdir(os.path.join('iota', 'modules')):
            if class_name == '__pycache__':
                continue
            # open each module folder in turn
            if os.path.isdir(os.path.join('iota', 'modules', class_name)):
                self.singletons[class_name] = None
                self._load_module(class_name)

    def _load_module(self, class_name: str):
        # Load the module and its commands into memory
        cfg_file = f'{class_name.lower()}.json'
        cfg_path = os.path.join(
            'iota', 'modules', class_name, cfg_file
        )
        try:
            with open(cfg_path, 'r') as cfg:
                config = json.load(cfg)
            # quick schema check
            if 'command_words' not in config.keys():
                raise Utils.ModuleError(
                    class_name,
                    'Improperly formatted config: No command words'
                )
            # store the processed regexes here as well for quick lookup
            command_regexes = Utils.parse_to_regexes(config)
            self.cmd_map[class_name] = command_regexes
            self.all_commands.extend(command_regexes)
        except json.JSONDecodeError as err:
            raise Utils.ModuleError(
                class_name,
                f'Improperly formatted config: Invalid JSON',
                inner=f'{err.msg} (Line {err.lineno})'
            )

    def run_module(self, command):
        found = False
        command = command.rstrip('.!?').lower()
        if command == 'stop' and self._mp3_is_running():
            self._stop_mp3()
            return None
        if not any([re.match(reg, command) for reg in self.all_commands]):
            # The command doesn't match any valid commands Iota knows
            return None
        # We matched something, let's do the thing
        for name, cmds in self.cmd_map.items():
            for regex in cmds:
                if re.match(regex, command):
                    # We found the Module/command that matches
                    found = True
                    try:
                        self._spawn_module(name, command, regex)
                    except Utils.ModuleError:
                        raise
                    break
            if found:
                break

    def _spawn_module(self, name, command, regex):
        try:
            # Dynamically import the Module
            mod_class = getattr(
                importlib.import_module(f'modules.{name}.{name}'), name
            )
            module = self.singletons[name]
            if module is None:
                # Instantiate the Module
                module = mod_class()
            # For BackgroundModules, we need to clear them
            if isinstance(module, BackgroundModule):
                module.set_callback(
                    lambda r=None: self._delist_module(name, r)
                )
                module.run(command, regex)
            else:
                response = module.run(command, regex)
                self._delist_module(name, response)
        except Utils.ModuleError:
            self.singletons[name] = None
            raise

    def _mp3_is_running(self):
        return 'pid' in self.player_data.keys()

    def _stop_mp3(self):
        if self._mp3_is_running():
            psutil.Process(self.player_data['pid']).send_signal(signal.SIGTERM)
        self.player_data = Manager().dict()
        self.resume_music()

    def _say(self, phrase):
        if '.mp3' in phrase:
            self.pause_music()
            # play mp3 file on repeat
            self.player = Process(
                target=_play_mp3,
                args=(self.player_data, phrase)
            )
            self.player.start()
            return
        with open('last_response.txt', 'w') as lr:
            lr.write(phrase)
        Utils.speak_phrase(self.speech_config, phrase)

    def _delist_module(self, module_name, response):
        self.singletons[module_name] = None
        # Modules that talk back should return the response str
        if response is not None and response != '':
            self._say(response)

    def pause_music(self):
        if self.singletons['GoogleMusic'] is None:
            return
        self.singletons['GoogleMusic'].pause_if_running()

    def resume_music(self):
        if self.singletons['GoogleMusic'] is None:
            return
        self.singletons['GoogleMusic'].resume_if_running()


def _play_mp3(shared, filename: str):
    file_path = os.path.join('iota', 'resources', filename)
    process = Popen(['mpg123', '--quiet', '-Z', file_path])
    shared['pid'] = process.pid
    process.wait()
