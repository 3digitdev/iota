from modules.Module import Module


class RepeatPhrase(Module):
    def __init__(self, pipe):
        super().__init__(self, pipe)

    def run(self, command: str, regex) -> str:
        try:
            last_response = ''
            with open('last_response.txt', 'r') as lr:
                last_response = lr.read()
            self.say(f'I said: {last_response}')
        except Exception as e:
            self.log_exception(e)
