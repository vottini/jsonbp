
from datetime import datetime

_defaults = {
	'format': "%Y-%m-%dT%H:%M:%S%z",
}


def _format(value, specs):
	return value.strftime(specs['format'])


def _parse(value, specs):
	sanedValue = str(value)
	parsed_date = datetime.strptime(sanedValue, specs['format'])
	return True, parsed_date


type_specs = {
	'name': 'instant',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}

