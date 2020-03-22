#!/usr/bin/env python3
import json
import os
from pathlib import Path
from bullet import VerticalPrompt, Input


def build_config(name: str, command: str, path: str):
    config = {
        "command_words": [command.lower().rstrip("?")]
    }
    with open(os.path.join(path, f"{name.lower()}.json"), "w") as cfg:
        json.dump(config, cfg, indent=4)


def build_module(name: str, path: str):
    contents = f"""from modules.Module import Module


class {name.capitalize()}(Module):
    def __init__(self):
        super().__init__(self)

    def run(self, command: str):
        pass
"""
    with open(os.path.join(path, f"{name.capitalize()}.py"), "w") as mod:
        mod.write(contents)


def main():
    print("Let's create a Module!")
    cli = VerticalPrompt([
        Input("Module Name:  "),
        Input("First Command:  ")
    ])
    result = cli.launch()
    name = result[0][1]
    command = result[1][1]
    # Create module folder
    path = os.path.join("..", "src", "modules", name.capitalize())
    os.mkdir(path)
    # Create init
    Path(os.path.join(path, '__init__.py')).touch()
    # Create basic config file
    build_config(name, command, path)
    # Create Module Class file
    build_module(name, path)


if __name__ == "__main__":
    main()
