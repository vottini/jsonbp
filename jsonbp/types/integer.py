
from .. import number
from .. import error_type
from .. import limits

_defaults = {
	'min': limits.lowestNumber,
	'max': limits.greatestNumber
}

def _format(value, specs):
	return str(value)

def _parse(value, specs):
	if not isinstance(value, number.WrappedNumber):
		return False, error_type.VALUE_PARSING

	intValue = int(value.strValue)
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


