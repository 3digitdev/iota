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

from modules.Module import Module
import utils.mod_utils as Utils

interrupted = False


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
        self.phrase = ''

    def store_phrase(self, phrase):
        self.succeeded = True
        self.phrase = phrase

    def error(self, error):
        self.succeeded = False
        self.error_msg = error


class Speech2Text(Module):
    def __init__(self):
        self.detector = snowboydecoder.HotwordDetector(
            decoder_model=os.path.join('iota', 'resources', 'Iota.pmdl'),
            sensitivity=0.3
        )
        self._setup_mq()

    def listen(self):
        print('Listening...')
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
        '''performs one-shot speech recognition from the default microphone'''
        # Creates a speech recognizer using microphone as audio input.
        # The default language is "en-us".
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=Utils.SPEECH_CONFIG
        )
        # Listen for a phrase from the microphone
        result = speech_recognizer.recognize_once()
        # Check the result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print(f'I heard: "{result.text}"')
            self.send_response(
                type='VoiceCommand',
                response=result.text
            )
        elif result.reason == speechsdk.ResultReason.NoMatch:
            self.send_error('No speech could be recognized')
        elif result.reason == speechsdk.ResultReason.Canceled:
            error = result.cancellation_details
            if error.reason == speechsdk.CancellationReason.Error:
                self.send_error(f'Cancelled.  Error: {error.error_details}')
            else:
                self.send_error(f'Cancelled: {error.reason}')
