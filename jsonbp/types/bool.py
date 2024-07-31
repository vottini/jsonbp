
import jsonbp

_defaults = {
	'coerce': True
}


def _format(value, specs):
	return "true" if value else "false"


def _parse(value, specs):
	if isinstance(value, jsonbp.unquoted_str):
		if value in ('true', 'false'):
			return True, value == "true"

	if not specs['coerce']:
		return False, {
			"error": jsonbp.ErrorType.VALUE_PARSING,
			"context": {}
		}

	# coercion attempts
	# check if it's 'null' or empty string

	if None == value or 0 == len(value):
		return True, False

	try:
		rawValue = float(value)
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

