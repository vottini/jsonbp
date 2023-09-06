
import jsonbp

_defaults = {
	'coerce': False
}


def _format(value, specs):
	return "true" if value else "false"


def _parse(value, specs):
	if isinstance(value, bool):
		return True, value

	if not specs['coerce']:
		return False, {
			"error": jsonbp.errorType.VALUE_PARSING,
			"context": {}
		}

	# coercion attempts
	# check if it's 'null' or empty string

	sanedValue = str(value) if value is not None else None
	if None == value or 0 == len(sanedValue):
		return True, False

	try:
		rawValue = float(sanedValue)
		# check if is effectively zero or NaN
		if 0 == rawValue or rawValue != rawValue:
			return True, False

	except Exception as e:
		# just an attempt, no problem
		# swallow this exception
		pass

	# if none of the above, then most likely
	# it's a truthy value

	return True, True


type_specs = {
	'name': 'bool',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}

