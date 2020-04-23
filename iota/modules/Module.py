import json
import os
import pika

from utils.mod_utils import (
    ModuleError,
    ModuleResponse,
    MQ_KEY,
    MQ_EXCHANGE,
    parse_to_regexes
)


class Module:
    def __init__(self, child, pipe):
        # Get the name of the module for later
        self.name = child.__class__.__name__
        self.pipe = pipe
        self.running_action = True
        path = os.path.join('iota', 'modules', self.name)
        # Load that module's config
        file_name = f'{self.name.lower()}.json'
        with open(os.path.join(path, file_name), 'r') as mcfg:
            config = json.load(mcfg)
        # Verify the config file has at least commands
        if 'command_words' not in config.keys():
            raise ModuleError(
                self.name,
                'Improperly formatted config: No command words'
            )
        # assign the regex-built commands to the Module
        child.commands = parse_to_regexes(config)
        if 'regexes' in config.keys():
            # Also assign the unprocessed regexes from config if needed
            child.regexes = config['regexes']
        self._setup_mq()

    def _setup_mq(self):
        self.conn = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost')
        )
        self.channel = self.conn.channel()
        self.channel.exchange_declare(MQ_EXCHANGE)

    def close(self):
        self.conn.close()

    def send_response(self, type: str, response: str):
        self.channel.basic_publish(
            exchange=MQ_EXCHANGE,
            routing_key=MQ_KEY,
            body=bytes(ModuleResponse(type, response))
        )

    def say(self, phrase):
        self.send_response('SpokenResponse', phrase)

    def send_error(self, error):
        self.send_response('ErrorResponse', error)

    def acknowledge(self):
        self.send_response('Acknowledge', None)

    def play_mp3(self, file):
        self.send_response('Mp3Response', file)

    def run(self, command: str, regex):
        pass

    def await_next_command(self):
        print(f'{self.name} awaiting next command...')
        while self.running_action:
            if self.pipe.poll(1):
                print(f'{self.name} heard from pipe!')
                args = self.pipe.recv()
                if isinstance(args, list) and len(args) == 2:
                    self.run(*args)

    def finish_action(self, callback=lambda: None):
        print(f'{self.name} finishing action')
        self.running_action = False
        callback()
