
import math
import jsonbp

nan = float('nan')
minus_infinity = float('-inf')
plus_infinity = float('+inf')

# for format options, see:
# https://cplusplus.com/reference/cstdio/printf/

_defaults = {
	'format': '%g',
	'atLeast': minus_infinity,
	'atMost': plus_infinity,
	'greaterThan': nan,
	'lessThan': nan,
	'allowNaN': False
}


def _format(value, specs):
	if value == minus_infinity: return "-Infinity"
	if value == plus_infinity: return "+Infinity"
	if value != value: return "NaN"

	strFormat = specs['format']
	return strFormat % value


def _parse(value, specs):
	sanedValue = value.replace('Infinity', 'inf')
	rawValue = float(sanedValue)

	if rawValue != rawValue:
		if specs['allowNaN']:
			return True, rawValue
			
		return False, {
			"error": jsonbp.errorType.OUTSIDE_RANGE,
			"context": {"value": rawValue}
		}

	checks = [
		lambda : not rawValue < specs['atLeast'],
		lambda : not rawValue > specs['atMost']
	]

	floor = specs['greaterThan']
	if not math.isnan(floor):
		check = lambda : rawValue > floor
		checks.append(check)

	ceiling = specs['lessThan']
	if not math.isnan(ceiling):
		check = lambda : rawValue < ceiling
		checks.append(check)

	for check in checks:
		if not check():
			return False, {
				"error": jsonbp.errorType.OUTSIDE_RANGE,
				"context": {"value": rawValue}
			}

	return True, rawValue


type_specs = {
	'name': 'float',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}

