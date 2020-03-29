import os

from modules.Module import Module


class RepeatPhrase(Module):
    def __init__(self):
        super().__init__(self)

    def run(self, command: str) -> str:
        last_response = ""
        with open("last_response.txt", "r") as lr:
            last_response = lr.read()
        return f"I said: {last_response}"
