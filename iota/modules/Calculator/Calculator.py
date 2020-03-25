import re

from modules.Module import Module
from utils.mod_utils import get_params


class Calculator(Module):
    def __init__(self):
        super().__init__(self)
        self.ors_reg = re.compile(self.regexes["operator"])
        self.ands_reg = re.compile(self.regexes["operand"])

    def run(self, command: str, regex) -> str:
        params = get_params(command, regex, self.regexes.keys())
        expression = params["expression"]
        if expression == "":
            return ""
        return self._calculate(expression)

    def _get_operator(self, op: str):
        op_map = {
            "+": {
                "others": ["plus"],
                "fn": lambda x, y: x + y
            },
            "-": {
                "others": ["minus"],
                "fn": lambda x, y: x - y
            },
            "*": {
                "others": ["times", "x"],
                "fn": lambda x, y: x * y
            },
            "/": {
                "others": ["divided by"],
                "fn": lambda x, y: x / y
            },
            "%": {
                "others": ["mod", "modulo"],
                "fn": lambda x, y: x % y
            },
            "^": {
                "others": ["**", "to the power of"],
                "fn": lambda x, y: x ** y
            }
        }
        for k, v in op_map.items():
            if op == k or op in v["others"]:
                return v["fn"]
        return None

    def _pemdas(self, op: str) -> int:
        add = ["plus", "+"]
        sub = ["minus", "-"]
        mult = ["times", "x", "*"]
        div = ["divided by", "/"]
        mod = ["mod", "modulo", "%"]
        exp = ["to the power of", "^"]
        if op in [*add, *sub]:
            return 1
        elif op in [*mult, *div, *mod]:
            return 2
        elif op in exp:
            return 3
        return 0

    def _peek(self, stack: list) -> str:
        return stack[-1] if stack else None

    def _in_to_post(self, command: str) -> list:
        operators = re.findall(self.ors_reg, command)
        operands = re.findall(self.ands_reg, command)
        postfix = []
        stack = ["#"]
        for i, operand in enumerate(operands):
            postfix.append(operand)
            if i == len(operators):
                break
            op = operators[i]
            if self._pemdas(op) > self._pemdas(self._peek(stack)):
                stack.append(op)
            else:
                while self._peek(stack) != "#" and \
                        (self._pemdas(op) <= self._pemdas(self._peek(stack))):
                    postfix.append(stack.pop())
                stack.append(op)
        while self._peek(stack) != "#":
            postfix.append(stack.pop())
        return postfix

    def _calculate(self, command):
        postfix = self._in_to_post(command)
        stack = []
        for token in postfix:
            if self.ors_reg.match(token):
                # Pull out a function to be called based on operator
                operator = self._get_operator(token)
                if operator is None:
                    break
                operand_2 = stack.pop()
                operand_1 = stack.pop()
                # execute the operator, but put the result back as a string
                stack.append(
                    str(
                        operator(float(operand_1), float(operand_2))
                    )
                )
            else:
                stack.append(token)
        # Don't need iota listing repeating forever... let's round it off
        if float(stack[0]).is_integer():
            return f"{stack[0].split('.')[0]}"
        return f"about {float(stack[0]):.6f}"
