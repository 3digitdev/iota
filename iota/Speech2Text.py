import os
import snowboydecoder
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

from modules.ModuleRunner import ModuleRunner
from modules.Module import ModuleError

interrupted = False
AZURE_KEY = os.environ["AZURE_KEY"]
AZURE_REGION = os.environ["AZURE_REGION"]


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


def interrupt_callback():
    global interrupted
    return interrupted


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


class Speech2Text(object):
    def __init__(self, wake_words: list):
        self.speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_KEY,
            region=AZURE_REGION
        )
        self.detector = snowboydecoder.HotwordDetector(
            decoder_model=os.path.join("iota", "resources", "Iota.pmdl"),
            sensitivity=0.3
        )
        self.runner = ModuleRunner(self.speech_config)

    def listen(self):
        print('Listening... Say "shut down" (or press Ctrl+C) to exit')
        # main loop
        self.detector.start(
            # Function to call when we detect the wake word
            detected_callback=self.detected_wake_word,
            # Function to call that interrupts the loop
            interrupt_check=interrupt_callback,
            # Time to sleep between loops in seconds
            sleep_time=0.03,
            # Amount of silence that's needed to stop recording phrase
            silent_count_threshold=7
        )
        self.detector.terminate()

    def detected_wake_word(self):
        """performs one-shot speech recognition from the default microphone"""
        # Creates a speech recognizer using microphone as audio input.
        # The default language is "en-us".
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config
        )
        # Listen for a phrase from the microphone
        result = speech_recognizer.recognize_once()
        # Check the result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print(f"I heard: {result.text}")
            try:
                self.runner.run_module(result.text)
            except ModuleError as err:
                print(f"Error in {err.module}:  {err.message}")
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized")
        elif result.reason == speechsdk.ResultReason.Canceled:
            error = result.cancellation_details
            print(f"Cancelled: {error.reason}")
            if error.reason == speechsdk.CancellationReason.Error:
                print(f"Error: {error.error_details}")
