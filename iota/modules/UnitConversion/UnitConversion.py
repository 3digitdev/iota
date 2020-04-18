import re
from pint import UnitRegistry
from pint.errors import \
    UndefinedUnitError, OffsetUnitCalculusError, DimensionalityError
from word2number.w2n import word_to_num

from modules.Module import Module
from utils.mod_utils import get_params


class UnitConversion(Module):
    def __init__(self):
        super().__init__(self)
        self.unit_reg = UnitRegistry()

    def run(self, command: str, regex) -> str:
        params = get_params(command, regex, self.regexes.keys())
        if any([p is None for p in params.values()]) or params.keys() == []:
            return ''
        # one useful thing for temperature
        before_unit = self._strip_degrees(params['before_unit'])
        after_unit = self._strip_degrees(params['after_unit'])
        try:
            before = self.unit_reg(before_unit)
            after = self.unit_reg(after_unit)
            if params['after_count'] != '':
                return self._convert(after, before, params['after_count'])
            elif params['before_count'] != '':
                return self._convert(before, after, params['before_count'])
            else:
                return ''
        except OffsetUnitCalculusError as err:
            print(err)
            return f'Conversion Error!'
        except UndefinedUnitError as err:
            return f'Undefined unit: {err}'
        except DimensionalityError as err:
            return f'Conversion Error:  {err}'

    def _strip_degrees(self, units):
        reg = re.compile(r'degree(?:s? |_)(?P<unit>.*)')
        match = re.match(reg, units)
        return units if match is None else match.group('unit')

    def _split_degrees(self, units, plural):
        if re.match(f'degree_.*', units):
            parts = units.split('_')
            if plural:
                return f'{parts[0]}s {parts[1]}'
            return " ".join(parts)
        return units

    def _convert(self, first, second, value):
        value = value.replace(',', '')
        if re.match(r'^an?$', value):
            value = 1
        first._magnitude = float(value)
        try:
            result = first.to(second)
            result._magnitude = self._string_to_num(result.magnitude)
            return self._format_response(first, result, value)
        except DimensionalityError:
            raise

    def _format_response(self, first, result, value):
        value = self._string_to_num(value)
        f_unit = self._split_degrees(str(first.units), value != 1)
        if 'degrees' not in f_unit and value != 1:
            f_unit += 's'
        r_unit = self._split_degrees(str(result.units), result.magnitude != 1)
        if 'degrees' not in r_unit and result.magnitude:
            r_unit += 's'
        return f'{value} {f_unit} is {result.magnitude} {r_unit}'

    def _string_to_num(self, s):
        chopped = float(f'{float(s):.4f}')
        if chopped.is_integer():
            return int(chopped)
        return chopped
