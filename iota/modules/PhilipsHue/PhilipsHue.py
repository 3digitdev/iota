import re
from typing import Callable
from word2number import w2n

from modules.Module import Module
from modules.PhilipsHue.HueController import HueController
from utils.mod_utils import get_params


class PhilipsHue(Module):
    def __init__(self):
        super().__init__(self)

    def run(self, command: str, regex) -> str:
        params = get_params(command, regex, self.regexes.keys())
        action_fn = self._pick_action(params)
        action_fn()
        self.acknowledge()

    def _pick_action(self, params: dict) -> Callable:
        # All the commands require the name
        name = params['name']
        if name == '':
            return lambda: None
        hue = HueController()
        if params['bright'] != '':
            # No matter what the state is, we're turning them on
            bright = self._parse_brightness(params['bright'])
            if bright == 0:  # jk, let's turn off light
                return lambda: hue.turn_off_group(name)
            else:  # turn on and set brightness
                return lambda: hue.turn_on_group(name, bright)
        if params['state'] != '':
            if params['state'].lower() == 'on':
                return lambda: hue.turn_on_group(name)
            elif params['state'].lower() == 'off':
                return lambda: hue.turn_off_group(name)
        return lambda: None

    def _parse_brightness(self, bright: str) -> int:
        reg = re.compile(r'(\d{1,3}|(?:\w+){1,2})(?: per ?cent|%)?')
        match = re.match(reg, bright)
        return w2n.word_to_num(match.groups()[0])
