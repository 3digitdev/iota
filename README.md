# Iota

_Home Automation using Python_

## Dependencies

- gTTS
- pyaudio
- SpeechRecognition
- word2number
- wakeonlan (used for Vizio Module)

For all of the above, run:

`python3 -m pip install gTTS pyaudio SpeechRecognition word2number wakeonlan`

- For `init_module.py`:
  - Bullet (`python3 -m pip install bullet`)

## Usage:

**From project root**, run `python3 iota`, then say something!

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

If you want your Module to give a spoken response, return the phrase to speak as a string from
the `run()` function in your Module.  Empty strings and/or `None` return values will result in no
speech after the Module finishes.

**For ideas on how to handle parameters on commands, see Vizio or PhilipsHue for examples!**

**Note that the `"regexes"` key will be required in your `.json` file for this!**
