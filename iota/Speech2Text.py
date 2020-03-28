import json
import time
from enum import Enum, auto
from speech_recognition import \
    Recognizer, AudioSource, Microphone, UnknownValueError, RequestError

from modules.ModuleRunner import ModuleRunner
from modules.Module import ModuleError


class PhraseResult(object):
    __slots__ = ['succeeded', 'error_msg', 'phrase']

    def __init__(self):
        self.succeeded = False
        self.error_msg = None
        self.phrase = ""

    def store_phrase(self, phrase):
        self.succeeded = True
        self.phrase = phrase

    def error(self, error):
        self.succeeded = False
        self.error_msg = error


class RecognizerSource(Enum):
    GOOGLE = auto()
    SPHINX = auto()


class Speech2Text(object):
    __slots__ = [
        'rec',
        'rec_fn',
        'current_audio',
        'filter',
        'filter_duration',
        'debug_mode',
        'mic',
        'shutdown',
        'wake_words',
        'module_runner'
    ]

    def __init__(
        self,
        recognizer: RecognizerSource,
        wake_words: list,
        filter: bool = False,
        filter_duration: float = 0.5,
        debug=False
    ):
        self.rec = Recognizer()
        self.rec_fn = {
            RecognizerSource.GOOGLE: lambda x: self.rec.recognize_google(**x),
            RecognizerSource.SPHINX: lambda x: self.rec.recognize_sphinx(**x)
        }[recognizer]
        self.wake_words = wake_words
        self.filter = filter
        self.filter_duration = filter_duration
        self.debug_mode = debug
        self.mic = Microphone()
        self.shutdown = False
        try:
            self.module_runner = ModuleRunner()
        except ModuleError:
            raise

    def active_listen(self):
        try:
            stop_fn = self.rec.listen_in_background(
                self.mic, self._process_phrase
            )
        except ModuleError:
            raise
        # Eventually we can use this to have it always running...
        # while True:
        # For now we will use 'shut down' as an 'off' command
        while not self.shutdown:
            time.sleep(0.1)
        stop_fn(wait_for_stop=False)

    def mic_to_text(self) -> PhraseResult:
        with self.mic as source:
            self.current_audio = self.rec.listen(source)
            return self._speech_to_text()

    def file_to_text(self, file: str) -> PhraseResult:
        self._process_audio(file)
        return self._speech_to_text()

    def _process_phrase(self, recognizer: Recognizer, audio: AudioSource):
        self.current_audio = audio
        # set debug=True to see the results that were detected
        result = self._speech_to_text()
        if result.succeeded:
            print(f"Heard phrase:\n  {result.phrase}")
            wake_word = self._check_wake_word(result.phrase)
            if wake_word:
                try:
                    self._parse_phrase(result.phrase, wake_word)
                except ModuleError:
                    raise
            # Temporary:  Allows us to shut it down with a command
            if result.phrase == 'shut down':
                self.shutdown = True
        else:
            print(f"Encountered an error:\n  {result.error_msg}")

    def _check_wake_word(self, phrase: str) -> str:
        for word in self.wake_words:
            if word in phrase:
                return word
        return None

    def _parse_phrase(self, phrase: str, wake_word: str):
        # Grabs everything AFTER the wake word (allowing for "hey [wake_word]")
        command = phrase[phrase.find(wake_word, 0) + len(wake_word):].strip()
        print(f"Processing command: [{command}]")
        try:
            self.module_runner.run_module(command)
        except ModuleError:
            raise

    def _speech_to_text(self) -> PhraseResult:
        result = PhraseResult()
        try:
            phrase = self.rec_fn({"audio_data": self.current_audio})
            result.store_phrase(phrase.lower())
        except RequestError as e:
            print(e)
            result.error("Recognizer API not reachable!")
        except UnknownValueError:
            result.error("Unintelligible speech!")
        return result

    def _stt_alternatives(self) -> str:
        return json.dumps(
            self.rec_fn({"audio_data": self.current_audio, "show_all": True}),
            indent=2
        )

    def _process_audio(self, audio_in: AudioSource):
        with audio_in as source:
            if self.filter:
                self._filter_audio(source)
            self.current_audio = self.rec.record(source)

    def _filter_audio(self, source: AudioSource):
        self.rec.adjust_for_ambient_noise(source, self.filter_duration)
