#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.
"""
Speech synthesis samples for the Microsoft Cognitive Services Speech SDK
"""
import os
try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    print("""
    Importing the Speech SDK for Python failed.
    Refer to
    https://docs.microsoft.com/azure/cognitive-services/speech-service/quickstart-text-to-speech-python for
    installation instructions.
    """)
    import sys
    sys.exit(1)


# Set up the subscription info for the Speech Service:
# Replace with your own subscription key and service region (e.g., "westus").
speech_key = os.environ["AZURE_KEY"]
service_region = os.environ["AZURE_REGION"]


def speech_synthesis_to_speaker():
    """performs speech synthesis to the default speaker"""
    # Creates an instance of a speech config with specified subscription key and service region.
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    # speech_config.speech_synthesis_voice_name = "Microsoft Server Speech Text to Speech Voice (en-US, AriaRUS)"
    speech_config.speech_synthesis_voice_name = "Microsoft Server Speech Text to Speech Voice (en-US, AriaNeural)"
    # Creates a speech synthesizer using the default speaker as audio output.
    # The default spoken language is "en-us".
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    # Receives a text from console input and synthesizes it to speaker.
    while True:
        print("Enter some text that you want to speak, Ctrl-Z to exit")
        try:
            text = input()
        except EOFError:
            break
        result = speech_synthesizer.speak_text_async(text).get()
        # Check result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Speech synthesized to speaker for text [{}]".format(text))
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))

speech_synthesis_to_speaker()
