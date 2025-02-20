
import jsonbp
import limits

_defaults = {
	'min': limits.lowestNumber,
	'max': limits.greatestNumber
}


def _format(value, specs):
	return str(value)


def _parse(value, specs):
	intValue = int(value)
	if not specs['min'] <= intValue <= specs['max']:
		return False, {
			"error": jsonbp.ErrorType.OUTSIDE_RANGE,
			"context": {"value": intValue}
		}

	return True, intValue


type_specs = {
	'name': 'Integer',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}


