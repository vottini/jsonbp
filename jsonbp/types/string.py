
import re
from .. import error_type

_defaults = {
	'minLength': 0,
	'maxLength': 1024,
	'format': r".*"
}

def _format(value, specs):
	return f'"{value}"'

def _parse(value, specs):
	if not isinstance(value, str):
		return False, error_type.VALUE_PARSING

	strLength = len(value)
	if not specs['minLength'] <= strLength <= specs['maxLength']:
		return False, {
			"error": error_type.INVALID_LENGTH,
			"context": { "length": strLength }
		}

	if re.search(specs['format'], value) is None:
		return False, {
			"error": error.INVALID_FORMAT,
			"context": {}
		}

	return True, value

type_specs = {
	'name': 'string',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}

