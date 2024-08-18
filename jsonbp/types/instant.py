
from datetime import datetime

_defaults = {
	'iso': True,
	'isoResolution': 'milliseconds',
	'format': "%Y-%m-%dT%H:%M:%S%z"
}

# allowed_resolutions:
# https://docs.python.org/3/library/datetime.html#datetime.datetime.isoformat

def _format(value, specs):
	try:
		if specs['iso']:
			resolution = specs['isoResolution']
			result = value.isoformat(timespec=resolution)
			return f'"{result}"'

		result = value.strftime(specs['format'])
		return f'"{result}"'

	except Exception as e:
		print(f"{value} GAVE ERROR:", repr(e))
		return False, {
			"error": jsonbp.ErrorType.VALUE_PARSING,
			"context": {}
		}


def _parse(value, specs):
	sanedValue = str(value)

	parsed_date = (
		datetime.fromisoformat(sanedValue) if specs['iso']
		else datetime.strptime(sanedValue, specs['format'])
	)

	return True, parsed_date


type_specs = {
	'name': 'instant',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}

