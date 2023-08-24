
from .. import error_type

_defaults = {
	'atLeast': float('-inf'),
	'atMost': float('+inf'),
	'greaterThan': float('-inf'),
	'lessThan': float('+inf')
}

def _format(value, specs):
	return str(value)

def _parse(value, specs):
	sanedValue = value.replace('Infinity', 'inf')
	rawValue = float(sanedValue)

	if (
		(not specs['atLeast'] <= rawValue <= specs['atMost']) or
		(not specs['greaterThan'] < rawValue < specs['lessThan'])
	) : return False, {
		"error": error_type.OUTSIDE_RANGE,
		"context": {"value": rawValue}
	}

	return True, rawValue

type_specs = {
	'name': 'float',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}

