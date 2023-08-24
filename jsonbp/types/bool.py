
from .. import error_type

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
			"error": error_type.VALUE_PARSING,
			"context": {}
		}

	# coercion attempt
	# check if is 'null' or empty string
	if None == value or 0 == len(value):
		return True, False

	try:
		rawValue = float(value)
		# check if is effectively zero or NaN
		if 0 == rawValue or rawValue != rawValue:
			return True, False

	except Exception as e:
		# it was just an attempt, no problem
		# just swallow this exception
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

