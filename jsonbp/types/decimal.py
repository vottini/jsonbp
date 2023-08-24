
import re
import datetime
from decimal import Decimal
import decimal

from .. import error_type
from .. import limits

_defaults = {
	'precision': 2,
	'min': Decimal(limits.lowestNumber).quantize(Decimal('0.01')),
	'max': Decimal(limits.greatestNumber).quantize(Decimal('0.01')),
	'decimal': '.',
	'separator': ''
}

roundingContext = decimal.Context(rounding=decimal.ROUND_DOWN)
specialChars = r'.^$*+?|'

# doesnt yet support indian style currency
# (at least formatting)

def _format(value, specs):
	return str(value)

def _parse(value, specs):
	grpSep = specs['separator']
	decSep = specs['decimal']

	if grpSep in specialChars: grpSep = f'\\{grpSep}'
	if decSep in specialChars: decSep = f'\\{decSep}'
	decimalPattern = f'^[+-]?\\d+({grpSep}\\d+)*({decSep}\\d+)?$'

	if None == re.match(decimalPattern, value):
		return False, {
			"error": error_type.VALUE_PARSING,
			"context": {}
		}

	sanedStrValue = (value
		.replace(specs['separator'], '')
		.replace(specs['decimal'], '.')
	)

	precision = f"1e-{specs['precision']}"
	rawValue = Decimal(sanedStrValue).quantize(Decimal(precision),
		context=roundingContext)

	if specs['min'] > rawValue or rawValue > specs['max']:
		return False, {
			"error": error_type.OUTSIDE_RANGE,
			"context": { "value": rawValue }
		}

	return True, rawValue

type_specs = {
	'name': 'decimal',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}

