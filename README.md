# Iota

_Home Automation using Python_

# TODO

- Add ability to mute music when listening to and processing a command
- Create method to automatically re-pair with TV [separate command!]
- Build a Docker Image for running Iota
  - Learn how to connect external speakers and microphones to a Docker Image
  - Learn how to automatically update Docker Image from latest release on GitHub
    - Publish to DockerHub through GitHub Actions?
- Find Speaker/Microphone to use with RasPi
  - [Microphone](https://respeaker.io/6_mic_array/)
  - [Speaker(s)](https://thepihut.com/pages/search-results?q=speaker)
    - Perhaps just use a nice bluetooth speaker??
- LONG TERM:  Learn how to make this Docker Image run on a phone??

# Future Module Ideas

- Spotify Module
- Module for sending slack messages through an iota-bot
- Module for storing/giving links to common searches (integrate with slackbot)

## Data Privacy Information

This assistant was built to handle wake-word detection entirely offline, using
Snowboy.  Once it hears the wake word, the microphone will record the first
"phrase" it hears, where a "phrase" anything up until a relatively short bout of
"silence" (not counting background audio, which should be mostly ignored).

The service then uses the data streamed from the microphone for that phrase and
sends the clip to Azure Cognitive Services for speech-to-text translation.

If you want to use this, and do not want to send data to Microsoft, you can opt
to trade in for a [Microsoft-provided Docker image](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/speech-container-howto), which can be hosted locally on
your own machine, and you can modify the calls to the Azure CogServ in the code
to instead call to this Docker image instead.  I make no guarantees on the quality
of translation, as I have not tested it for myself.  Caveat emptor.

## Usage:

### Local

**From project root**, run `python3 iota`, then say something!

### Docker

**TODO!!**

## Creating a Module:

**From project root**, run `python3 tools/init_module.py`.

### CLI

**Module Name:**  This should be a space-separated form of the name, so like
"philips hue" for the PhilipsHue Module.

**First Command:**  This isn't really required, but you can add this to put a
placeholder command in the config file.

This will do the following for a module you call `hello world`:
```
iota
 ├─ modules
 │   ├─ HelloWorld
 │   │   ├─ __init__.py
 │   │   ├─ HelloWorld.py
 │   │   └─ helloworld.json
 │   └─ ...
 └─ ...
```

From here, you can implement your new Module.  The `run()` function in your module
is inherited from the base `Module`, and is called by the `ModuleRunner` if any of your
commands are matched by the incoming spoken phrase.

If you want your Module to give a spoken response, you use the built-in `Module.say()` function
to speak a phrase as a result.  You can also play a saved mp3 file, throw an error, or just
"acknowledge" the request (currently a NoOp -- eventually will play a tone)

**For ideas on how to handle parameters on commands, see Vizio or PhilipsHue for examples! (Note that the `"regexes"` key will be required in your `.json` file for this!)**


# Attribution

The `acknowledge.mp3` and `error.mp3` files are licensed under [Creative Commons](https://creativecommons.org/licenses/by/4.0/legalcode) through [NotificationSounds.com](https://notificationsounds.com/).

The files are located at [Me Too (acknowledge)](https://notificationsounds.com/notification-sounds/me-too-603) and [Case Closed (error)](https://notificationsounds.com/notification-sounds/case-closed-531)

Both were modified slightly to remove the silence at the end, but the original tones are still the same.
