import re
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


def parse_to_regexes(config: dict) -> list:
    reg = re.compile(r'\{[^\}]+\}')
    commands = []
    for command in config["command_words"]:
        for placeholder in reg.findall(command):
            name = placeholder[1:-1]
            command = command.replace(
                placeholder,
                f"(?P<{name}>{config['regexes'][name]})"
            )
        commands.append(re.compile(f"^{command}$"))
    return commands


def get_params(command, regex, groups) -> dict:
    match = re.match(regex, command)
    params = {}
    for group_name in groups:
        try:
            params[group_name] = match.group(group_name)
        except IndexError:
            params[group_name] = ""
    return params


def process_file(config, filename) -> str:
    """
    performs one-shot speech recognition with input from an audio file
    Reference:  https://github.com/Azure-Samples/cognitive-services-speech-sdk/blob/master/samples/python/console/speech_sample.py
    """
    audio_config = speechsdk.audio.AudioConfig(filename=filename)
    # Creates a speech recognizer using a file as audio input.
    # The default language is "en-us".
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=config,
        audio_config=audio_config
    )
    # Process the input
    result = speech_recognizer.recognize_once()
    # Check the result
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        # TODO:  Call out to ModuleRunner!
        out = result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        out = f"No speech could be recognized"
    elif result.reason == speechsdk.ResultReason.Canceled:
        error = result.cancellation_details
        out = f"Cancelled: {error.reason}"
        if error.reason == speechsdk.CancellationReason.Error:
            out = f"Error: {error.error_details}"
    return out


def speak_phrase(config, phrase) -> None:
    # Female Australian (Catherine)
    # self.speech_config.speech_synthesis_voice_name = \
    #     "Microsoft Server Speech Text to Speech Voice (en-AU, Catherine)"
    # Female US (Aria)
    config.speech_synthesis_voice_name = \
        "Microsoft Server Speech Text to Speech Voice (en-US, AriaRUS)"
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=config)
    # Try to say the response
    result = speech_synthesizer.speak_text_async(phrase).get()
    # Checks result.
    if result.reason == speechsdk.ResultReason.Canceled:
        error = result.cancellation_details
        print(f"Speech synthesis canceled: {error.reason}")
        if error.reason == speechsdk.CancellationReason.Error:
            if error.error_details:
                print(f"Error details: {error.error_details}")
