
import re
import jsonbp

_defaults = {
	'minLength': 0,
	'maxLength': 1024,
	'format': r".*"
}


def _format(value, specs):
	escaped = value.replace('"', '\\"')
	return f'"{escaped}"'


def _parse(value, specs):
	if isinstance(value, jsonbp.unquoted_str):
		return False, jsonbp.ErrorType.VALUE_PARSING

	strLength = len(value)
	if not specs['minLength'] <= strLength <= specs['maxLength']:
		return False, {
			"error": jsonbp.ErrorType.INVALID_LENGTH,
			"context": { "length": strLength }
		}

	fullFormat = f"^{specs['format']}$"
	if re.search(fullFormat, value) is None:
		return False, {
			"error": jsonbp.ErrorType.INVALID_FORMAT,
			"context": {}
		}

	return True, value


type_specs = {
	'name': 'String',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}

