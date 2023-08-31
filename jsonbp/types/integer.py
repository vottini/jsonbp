
from .. import error_type
from .. import numbers

_defaults = {
	'min': numbers.lowest,
	'max': numbers.greatest
}


def _format(value, specs):
	return str(value)


def _parse(value, specs):
	intValue = int(value)
	if not specs['min'] <= intValue <= specs['max']:
		return False, {
			"error": error_type.OUTSIDE_RANGE,
			"context": {"value": intValue}
		}

	return True, intValue


type_specs = {
	'name': 'integer',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}


