import re

from modules.Module import Module
from utils.mod_utils import get_params
from utils.rpn import RPNCalculator


class Calculator(Module):
    def __init__(self):
        super().__init__(self)
        self.ors_reg = re.compile(self.regexes['operator'])
        self.ands_reg = re.compile(self.regexes['operand'])

    def run(self, command: str, regex) -> str:
        result = None
        params = get_params(command, regex, self.regexes.keys())
        expression = params['expression']
        if expression == '':
            return
        calculator = RPNCalculator()
        value = calculator.calculate(expression)
        if float(value).is_integer():
            result = f'{value.split(".")[0]}'
        else:
            result = f'about {float(value):.6f}'
        if result is not None:
            self.say(result)
        self.finish_action()
