import re
from subprocess import Popen
from enum import Enum
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


# --- CONSTANTS --- #
import os
MQ_EXCHANGE = os.environ['MQ_EXCHANGE']
MQ_KEY = os.environ['MQ_KEY']
AZURE_KEY = os.environ['AZURE_KEY']
AZURE_REGION = os.environ['AZURE_REGION']
SPEECH_CONFIG = speechsdk.SpeechConfig(
    subscription=AZURE_KEY,
    region=AZURE_REGION
)
# ----------------- #


# --- MODULE STUFF --- #
class ResponseType():
    WakeWord = 'WakeWord',
    VoiceCommand = 'VoiceCommand',
    SpokenResponse = 'SpokenResponse',
    Mp3Response = 'Mp3Response',
    Acknowledge = 'Acknowledge',
    ErrorResponse = 'ErrorResponse'


class ModuleResponse:
    __slots__ = ['type', 'data']

    def __init__(self, type: str, data: str):
        self.type = type
        self.data = data

    def __str__(self):
        return f'{self.type}|{self.data}'

    def __bytes__(self):
        return bytes(str(self), encoding='utf-8')


class ModuleError(Exception):
    def __init__(self, module, message, inner=''):
        self.module = module
        self.message = message
        if inner != '':
            self.message += f'\n    {inner}'
# -------------------- #


def response_from_str(str):
    parts = str.decode('utf-8').split('|')
    return ModuleResponse(parts[0], parts[1])


def parse_to_regexes(config: dict) -> list:
    reg = re.compile(r'\{[^\}]+\}')
    commands = []
    for command in config['command_words']:
        for placeholder in reg.findall(command):
            name = placeholder[1:-1]
            command = command.replace(
                placeholder,
                f'(?P<{name}>{config["regexes"][name]})'
            )
        commands.append(re.compile(f'^{command}$'))
    return commands


def get_params(command, regex, groups) -> dict:
    match = re.match(regex, command)
    params = {}
    for group_name in groups:
        try:
            params[group_name] = match.group(group_name)
        except IndexError:
            params[group_name] = ''
    return params


def speak_phrase(phrase) -> None:
    # Female Australian (Catherine)
    # self.speech_config.speech_synthesis_voice_name = \
    #     "Microsoft Server Speech Text to Speech Voice (en-AU, Catherine)"
    # Female US (Aria)
    # config.speech_synthesis_voice_name = \
    #     "Microsoft Server Speech Text to Speech Voice (en-US, AriaRUS)"
    # NEURAL Female US (Aria)
    SPEECH_CONFIG.speech_synthesis_voice_name = \
        "Microsoft Server Speech Text to Speech Voice (en-US, AriaNeural)"
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=SPEECH_CONFIG
    )
    # Try to say the response
    result = speech_synthesizer.speak_text_async(phrase).get()
    # Checks result.
    if result.reason == speechsdk.ResultReason.Canceled:
        error = result.cancellation_details
        print(f'Speech synthesis canceled: {error.reason}')
        if error.reason == speechsdk.CancellationReason.Error:
            if error.error_details:
                print(f'Error details: {error.error_details}')


def _play_mp3(filename: str, shared=None, repeat=False):
    file_path = os.path.join('iota', 'resources', filename)
    if repeat:
        args = ['mpg123', '--quiet', '-Z', file_path]
    else:
        args = ['mpg123', '--quiet', file_path]
    process = Popen(args)
    if shared is not None:
        shared['pid'] = process.pid
    process.wait()


def is_rounded_whole_number(num_str: str):
    return float(f'{float(num_str):.6f}').is_integer()


def trim_zeroes(num_str: str):
    reg = re.compile(r'^(?:about )?(?P<trimmed>\d+\.\d*[1-9])[0]+$')
    result = re.match(reg, num_str)
    return num_str if result is None else result.groups()[0]
