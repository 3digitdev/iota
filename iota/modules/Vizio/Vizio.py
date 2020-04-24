import re
from typing import Callable
from word2number import w2n

from modules.Module import Module
from modules.Vizio.VizioController import VizioController
from utils.mod_utils import get_params


class Vizio(Module):
    def __init__(self, pipe):
        super().__init__(self, pipe)

    def run(self, command: str, regex) -> str:
        try:
            params = get_params(command, regex, self.regexes.keys())
            action_fn = self._pick_action(params)
            action_fn()
        except Exception as e:
            self.log_exception(e)

    def _pick_action(self, params) -> Callable:
        action = params['action']
        vizio = VizioController()
        if action == 'turn on':
            return lambda: vizio.turn_on()
        elif action == 'turn off':
            return lambda: vizio.turn_off()
        if params['input'] != '':
            reg = re.compile(self.regexes['input'])
            if re.match(reg, params['input']):
                num_str = params['input'].split(' ')[-1]
                if re.match(r'\d+', num_str):
                    num = int(num_str)
                else:
                    num = str(w2n.word_to_num(params['input'].split(' ')[-1]))
            else:
                return lambda: None
            return lambda: vizio.switch_input(f'HDMI-{num}')
