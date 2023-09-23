
import jsonbp

def _format(value, specs):
	return str(value)


def _parse(value, specs):
	intValue = int(value)
	if intValue % 2 == 0:
		return False, {
			"error": jsonbp.errorType.OUTSIDE_RANGE,
			"context": {"value": intValue}
		}

	return True, intValue


type_specs = {
	'name': 'odd',
	'parser': _parse,
	#'formatter': _format,
	'defaults': dict()
}


