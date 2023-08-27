
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
	'separator': '',
	'indian_format': False,
	'prefix': "",
	'suffix': ""
}

roundingContext = decimal.Context(rounding=decimal.ROUND_DOWN)
specialChars = r'.^$*+?|'

def _format(value, specs):
	decimalMark = specs['decimal']
	separator = specs['separator']

	rawString = str(value)
	parts = rawString.split('.')
	integerPart = parts[0]

	if '' != separator and len(integerPart) > 3:
		hundredths = integerPart[-3:]
		thousandths = integerPart[:-3]

		groupSize = 3 if not specs['indian_format'] else 2
		leadingSize = len(thousandths) % groupSize
		leading = thousandths[:leadingSize]

		remaining = thousandths[leadingSize:]
		separated = re.findall(".{" + str(groupSize) + "}", remaining)
		thousandths = (leading, *separated) if leadingSize > 0 else separated
		integerPart = separator.join((*thousandths, hundredths))

	decimalPart = parts[1]
	content = (decimalMark.join([integerPart, decimalPart])
		if len(parts) > 1
		else integerPart)

	parts = ([ part
		for part in [ specs['prefix'], content, specs['suffix'] ]
		if len(part) > 0
	])

	formattedParts = "".join(parts)
	needsQuotes = len(parts) > 1 or '' != separator or '.' != decimalMark
	return f'"{formattedParts}"' if needsQuotes else formattedParts

def _parse(value, specs):
	decimalMark = specs['decimal']
	separator = specs['separator']

	if separator in specialChars: separator = f'\\{separator}'
	if decimalMark in specialChars: decimalMark = f'\\{decimalMark}'
	decimalPattern = f'^[+-]?\\d+({separator}\\d+)*({decimalMark}\\d+)?$'

	sanedValue = str(value)
	if None == re.match(decimalPattern, sanedValue):
		return False, {
			"error": error_type.VALUE_PARSING,
			"context": {}
		}

	sanedStrValue = (sanedValue
		.replace(decimalMark, '.')
		.replace(separator, '')
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

