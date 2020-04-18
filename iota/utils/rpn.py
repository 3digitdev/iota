import re


class RPNCalculator(object):
    def __init__(self, operands_reg='\\d+'):
        self.ors_reg = re.compile(r'(?:times|x|\*|divided by|\/|mod(?:ul(?:o|us))?|\%|plus|\+|minus|\-|to the power of|\^)')
        self.ands_reg = re.compile(operands_reg)

    def _get_operator(self, op: str):
        op_map = {
            '+': {
                'others': ['plus'],
                'fn': lambda x, y: x + y
            },
            '-': {
                'others': ['minus'],
                'fn': lambda x, y: x - y
            },
            '*': {
                'others': ['times', 'x'],
                'fn': lambda x, y: x * y
            },
            '/': {
                'others': ['divided by'],
                'fn': lambda x, y: x / y
            },
            '%': {
                'others': ['mod', 'modulo'],
                'fn': lambda x, y: x % y
            },
            '^': {
                'others': ['**', 'to the power of'],
                'fn': lambda x, y: x ** y
            }
        }
        for k, v in op_map.items():
            if op == k or op in v['others']:
                return v['fn']
        return None

    def _pemdas(self, op: str) -> int:
        add = ['plus', '+']
        sub = ['minus', '-']
        mult = ['times', 'x', '*']
        div = ['divided by', '/']
        mod = ['mod', 'modulo', '%']
        exp = ['to the power of', '^']
        if op in [*add, *sub]:
            return 1
        elif op in [*mult, *div, *mod]:
            return 2
        elif op in exp:
            return 3
        return 0

    def _peek(self, stack: list) -> str:
        return stack[-1] if stack else None

    def _in_to_post(self, expression: str) -> list:
        operators = re.findall(self.ors_reg, expression)
        operands = re.findall(self.ands_reg, expression)
        postfix = []
        stack = ['#']
        for i, operand in enumerate(operands):
            postfix.append(operand)
            if i == len(operators):
                break
            op = operators[i]
            if self._pemdas(op) > self._pemdas(self._peek(stack)):
                stack.append(op)
            else:
                while self._peek(stack) != '#' and \
                        (self._pemdas(op) <= self._pemdas(self._peek(stack))):
                    postfix.append(stack.pop())
                stack.append(op)
        while self._peek(stack) != '#':
            postfix.append(stack.pop())
        return postfix

    def calculate(self, expression, fn=lambda n: n):
        postfix = self._in_to_post(expression)
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
                stack.append(fn(token))
        return stack[0]
