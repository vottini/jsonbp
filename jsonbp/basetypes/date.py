
from datetime import date

_defaults = {
	'format': "%Y-%m-%d"
}


def _format(value, specs):
	result = value.strftime(specs['format'])
	return f'"{result}"'


def _parse(value, specs):
	str_value = str(value)
	parsed_date = date.fromisoformat(str_value)
	return True, parsed_date


type_specs = {
	'name': 'Date',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}

