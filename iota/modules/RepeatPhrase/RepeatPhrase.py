import os

from modules.Module import Module


class RepeatPhrase(Module):
    def __init__(self):
        super().__init__(self)

    def run(self, command: str) -> str:
        os.system('mpg123 last_command.mp3')
        return None
