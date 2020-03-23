import re
from typing import Callable
from word2number import w2n

from modules.Module import Module
from modules.Vizio.VizioController import VizioController


class Vizio(Module):
    def __init__(self):
        super().__init__(self)

    def run(self, command: str, regex) -> str:
        match = re.match(regex, command)
        params = {}
        for group_name in self.regexes.keys():
            try:
                params[group_name] = match.group(group_name)
            except IndexError:
                params[group_name] = ""
        action_fn = self._pick_action(params)
        action_fn()
        return ""

    def _pick_action(self, params) -> Callable:
        action = params["action"]
        vizio = VizioController()
        if action == "turn on":
            return lambda: vizio.turn_on()
        elif action == "turn off":
            return lambda: vizio.turn_off()
        if params["input"] != "":
            reg = re.compile(r'hdmi (?:\w+|\d)')
            if re.match(reg, params["input"]):
                num = str(w2n.word_to_num(params["input"].split(' ')[1]))
            else:
                return lambda: None
            return lambda: vizio.switch_input(f"HDMI-{num}")
