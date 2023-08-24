
from datetime import datetime
from .. import error_type

_defaults = {
	'format': "%Y-%m-%dT%H:%M:%S.%f%z",
}

def _format(value, specs):
	return value.strftime(specs['format'])

def _parse(value, specs):
	parsed_date = datetime.strptime(value, specs['format'])
	return True, parsed_date

type_specs = {
	'name': 'instant',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}
