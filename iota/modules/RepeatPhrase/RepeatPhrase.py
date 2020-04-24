from modules.Module import Module


class RepeatPhrase(Module):
    def __init__(self, pipe):
        super().__init__(self, pipe)

    def run(self, command: str, regex) -> str:
        last_response = ''
        with open('last_response.txt', 'r') as lr:
            last_response = lr.read()
        self.say(f'I said: {last_response}')
        self.finish_action()
