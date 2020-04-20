import json
import os
import pika

from utils.mod_utils import (
    ModuleError,
    ModuleResponse,
    ResponseType,
    MQ_KEY,
    MQ_EXCHANGE,
    parse_to_regexes
)


class Module:
    def __init__(self, child):
        # Get the name of the module for later
        module = child.__class__.__name__
        path = os.path.join('iota', 'modules', module)
        # Load that module's config
        with open(os.path.join(path, f'{module.lower()}.json'), 'r') as mcfg:
            config = json.load(mcfg)
        # Verify the config file has at least commands
        if 'command_words' not in config.keys():
            raise ModuleError(
                module,
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
