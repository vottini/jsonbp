
import re
import jsonbp

_defaults = {
	'minLength': 0,
	'maxLength': 1024,
	'format': r".*"
}


def _format(value, specs):
	return f'"{value}"'


def _parse(value, specs):
	if isinstance(value, jsonbp.unquoted_str):
		return False, jsonbp.ErrorType.VALUE_PARSING

	strLength = len(value)
	if not specs['minLength'] <= strLength <= specs['maxLength']:
		return False, {
			"error": jsonbp.ErrorType.INVALID_LENGTH,
			"context": { "length": strLength }
		}

	fullFormat = fr"^{specs['format']}$"
	if re.search(fullFormat, value) is None:
		return False, {
			"error": jsonbp.ErrorType.INVALID_FORMAT,
			"context": {}
		}

	return True, value


type_specs = {
	'name': 'string',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}

