import random
import re

from modules.Module import Module
from utils.mod_utils import get_params
from utils.rpn import RPNCalculator


class DiceRoller(Module):
    def __init__(self):
        super().__init__(self)

    def run(self, command: str, regex) -> str:
        result = None
        params = get_params(command, regex, self.regexes.keys())
        if command == 'flip a coin':
            result = random.choice(['heads', 'tails'])
        elif command == 'roll a dice':
            result = str(random.randint(1, 6))
        else:
            # Dice expression
            result = self.parse_dice_expression(params['expression'])
            if float(result).is_integer():
                result = f'{result.split(".")[0]}'
            result = f'{float(result):.6f}'
        if result is not None:
            self.say(result)
        self.finish_action()

    def parse_dice_expression(self, expression):
        expression = expression.replace(' ', '')
        dice_reg = re.compile(self.regexes['dice'])

        def calc_if_dice(value):
            match = dice_reg.match(value)
            if match is not None:
                count, dice = match.groups()
                total = 0
                for i in range(int(count)):
                    total += random.randint(1, int(dice))
                return str(total)
            return value

        rpn_calc = RPNCalculator(operands_reg='\\d*\\s*d?\\s*\\d+')
        return rpn_calc.calculate(expression, calc_if_dice)
