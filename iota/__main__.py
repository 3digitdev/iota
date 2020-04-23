#!/usr/bin/env python3
import pika
import os
import json
import re
import importlib
import psutil
import signal
from multiprocessing import Process, Manager, Pipe

import utils.mod_utils as Utils
from Speech2Text import Speech2Text


class RunningModule:
    def __init__(self, process: Process, pipe: Pipe):
        self.process = process
        self.pid = process.pid
        self.pipe = pipe

    def is_alive(self):
        return self.process is not None and self.process.is_alive()

    def send(self, data: list):
        self.pipe.send(data)

    def kill(self):
        self.pipe.close()
        self.process.terminate()


class Iota(object):
    def __init__(self):
        # maps each module name to a list of its regexed commands
        self.cmd_map = {}
        # all valid commands for Iota, for quick lookup
        self.all_commands = []
        # This is used for tracking running instances so we don't replicate
        # Also is helpful for Background Modules!
        self.singletons = {}
        # Playing mp3 stuff
        self.player = None
        self.shared_data = Manager().dict()
        # Load all Modules
        for class_name in os.listdir(os.path.join('iota', 'modules')):
            if class_name == '__pycache__':
                continue
            # open each module folder in turn
            if os.path.isdir(os.path.join('iota', 'modules', class_name)):
                self.singletons[class_name] = None
                self._load_module(class_name)
        self._setup_mq()

    def _load_module(self, class_name: str):
        # Load the module and its commands into memory
        cfg_file = f'{class_name.lower()}.json'
        cfg_path = os.path.join(
            'iota', 'modules', class_name, cfg_file
        )
        try:
            with open(cfg_path, 'r') as cfg:
                config = json.load(cfg)
            # quick schema check
            if 'command_words' not in config.keys():
                raise Utils.ModuleError(
                    class_name,
                    'Improperly formatted config: No command words'
                )
            # store the processed regexes here as well for quick lookup
            command_regexes = Utils.parse_to_regexes(config)
            self.cmd_map[class_name] = command_regexes
            self.all_commands.extend(command_regexes)
        except json.JSONDecodeError as err:
            raise Utils.ModuleError(
                class_name,
                f'Improperly formatted config: Invalid JSON',
                inner=f'{err.msg} (Line {err.lineno})'
            )

    def _setup_mq(self):
        # --- RabbitMQ/Pika Setup --- #
        params = pika.ConnectionParameters()
        self.conn = pika.SelectConnection(
            params, on_open_callback=self.on_connected
        )
        try:
            # Loop so we can communicate with RabbitMQ
            self.conn.ioloop.start()
        except KeyboardInterrupt:
            # Gracefully close the connection
            self.conn.close()
        # --- End RabbitMQ/Pika Setup --- #

    # --- RabbitMQ/Pika Functions --- #
    def on_connected(self, conn):
        conn.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        self.channel = channel
        self.channel.exchange_declare(exchange=Utils.MQ_EXCHANGE)
        self.channel.queue_purge(Utils.MQ_KEY)
        self.channel.queue_bind(
            queue=Utils.MQ_KEY,
            exchange=Utils.MQ_EXCHANGE,
            callback=self.on_queue_declared
        )
        self.listener = Speech2Text()
        listen_proc = Process(target=self.listener.listen)
        listen_proc.start()

    def on_queue_declared(self, frame):
        self.channel.basic_consume(
            queue=Utils.MQ_KEY,
            on_message_callback=self.consume,
            auto_ack=True
        )
    # --- End RabbitMQ/Pika Functions --- #

    def consume(self, channel, method, header, body):
        response = Utils.response_from_str(body)
        if response.type == 'VoiceCommand':
            # Received a command from the Listener
            self.run_module(response.data)
        elif response.type == 'SpokenResponse':
            # Received a response from one of the Modules
            with open('last_response.txt', 'w') as lr:
                lr.write(response.data)
            Utils.speak_phrase(response.data)
        elif response.type == 'Mp3Response':
            if '.mp3' not in response.data:
                return
            self.pause_music()
            # play mp3 file on repeat
            self.player = Process(
                target=Utils._play_mp3,
                args=(self.shared_data, response.data)
            )
            self.player.start()
        elif response.type == 'Acknowledge':
            # TODO:  Properly handle some acknowledgement tone
            pass
        elif response.type == 'ErrorResponse':
            raise Utils.ModuleError('ModuleRunner', response.data)
        else:
            raise Utils.ModuleError(
                'ModuleRunner',
                f'The ResponseType {response.type} is not supported',
                inner=response.data
            )

    def run_module(self, command):
        found = False
        command = command.rstrip('.!?').lower()
        # TODO: CHANGE THIS?
        if command == 'stop' and self._mp3_is_running():
            self._stop_mp3()
            return None
        if not any([re.match(reg, command) for reg in self.all_commands]):
            # The command doesn't match any valid commands Iota knows
            return None
        # We matched something, let's do the thing
        for name, cmds in self.cmd_map.items():
            for regex in cmds:
                if re.match(regex, command):
                    # We found the Module/command that matches
                    found = True
                    try:
                        self._spawn_module(name, command, regex)
                    except Utils.ModuleError:
                        raise
                    break
            if found:
                break

    def _spawn_module(self, name, command, regex):
        try:
            # Dynamically import the Module
            mod_class = getattr(
                importlib.import_module(f'modules.{name}.{name}'), name
            )
            module = self.singletons[name]
            print(f'Retrieved {module} from singletons')
            if module is None or not module.is_alive():
                print(f'{name} does not exists! Creating...')
                # Instantiate the Module
                parent_conn, child_conn = Pipe()
                mod_obj = mod_class(child_conn)
                mod_process = Process(
                    target=mod_obj.run,
                    args=(command, regex)
                )
                mod_process.start()
                self.singletons[name] = RunningModule(mod_process, parent_conn)
            elif isinstance(module, RunningModule):
                print(f'{name} exists!  Sending command [{command}, {regex}]')
                module.send([command, regex])
        except Utils.ModuleError:
            self.singletons[name] = None
            raise

    def _mp3_is_running(self):
        return 'pid' in self.shared_data.keys()

    def _stop_mp3(self):
        if self._mp3_is_running():
            psutil.Process(self.shared_data['pid']).send_signal(signal.SIGTERM)
        self.shared_data = Manager().dict()
        self.resume_music()

    def pause_music(self):
        if self.singletons['GoogleMusic'] is None:
            return
        self.singletons['GoogleMusic'].pause_if_running()

    def resume_music(self):
        if self.singletons['GoogleMusic'] is None:
            return
        self.singletons['GoogleMusic'].resume_if_running()


def main():
    try:
        Iota()
    except Utils.ModuleError as err:
        print(f'Your {err.module} module has an error:\n  {err.message}')


if __name__ == '__main__':
    main()
