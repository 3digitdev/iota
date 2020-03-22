import json
import time
from enum import Enum, auto
from speech_recognition import \
    Recognizer, AudioSource, Microphone, UnknownValueError, RequestError


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
        'shutdown'
    ]

    def __init__(
        self,
        recognizer: RecognizerSource,
        filter: bool = False,
        filter_duration: float = 0.5,
        debug=False
    ):
        self.rec = Recognizer()
        self.rec_fn = {
            RecognizerSource.GOOGLE: lambda x: self.rec.recognize_google(**x),
            RecognizerSource.SPHINX: lambda x: self.rec.recognize_sphinx(**x)
        }[recognizer]
        self.filter = filter
        self.filter_duration = filter_duration
        self.debug_mode = debug
        self.mic = Microphone()
        self.shutdown = False

    def active_listen(self):
        stop_fn = self.rec.listen_in_background(self.mic, self._process_phrase)
        # Eventually we can use this to have it always running...
        # while True:
        # For now we will use 'shut down' as an 'off' command
        while not self.shutdown:
            time.sleep(0.1)
        stop_fn(wait_for_stop=False)

    def mic_to_text(self):
        with self.mic as source:
            self.current_audio = self.rec.listen(source)
            return self._speech_to_text()

    def file_to_text(self, file: str):
        self._process_audio(file)
        return self._speech_to_text()

    def _process_phrase(self, recognizer, audio):
        self.current_audio = audio
        result = self._speech_to_text(debug=True)
        print(result.succeeded)
        if result.succeeded:
            print(f"Heard phrase:\n  {result.phrase}")
        else:
            print(f"Encountered an error:\n  {result.error_msg}")

    def _speech_to_text(self, debug=False):
        result = PhraseResult()
        try:
            if debug:
                phrase = self._stt_alternatives()
            else:
                phrase = self.rec_fn({"audio_data": self.current_audio})
            # TODO: Logic here for listening for wake word!

            # Temporary:  Allows us to shut it down with a command
            if phrase == 'shut down':
                self.shutdown = True
            result.store_phrase(phrase)
        except RequestError:
            result.error("Recognizer API not reachable!")
        except UnknownValueError:
            result.error("Unintelligible speech!")
        return result

    def _stt_alternatives(self):
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
