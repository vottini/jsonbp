
import re
import datetime
from decimal import Decimal
import decimal

import jsonbp
import limits

_defaults = {
	'precision': 2,
	'min': Decimal(limits.lowestNumber).quantize(Decimal('0.01')),
	'max': Decimal(limits.greatestNumber).quantize(Decimal('0.01')),
	'decimal': '.',
	'separator': '',
	'indianFormat': False,
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

		groupSize = 3 if not specs['indianFormat'] else 2
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

	needsQuotes = (
		len(parts) > 1 or
		'.' != decimalMark or
		'' != separator)

	formattedParts = "".join(parts)
	return (f'"{formattedParts}"' if needsQuotes
		else formattedParts)


def _parse(value, specs):
	sanedValue = (str(value)
		.removeprefix(specs['prefix'])
		.removesuffix(specs['suffix'])
	)

	decimalMark = specs['decimal']
	if decimalMark in specialChars:
		decimalMark = f'\\{decimalMark}'

	separator = specs['separator']
	if separator in specialChars:
		separator = f'\\{separator}'

	decimalPattern = f'^[+-]?\\d+({separator}\\d+)*({decimalMark}\\d+)?$'
	if None == re.match(decimalPattern, sanedValue):
		return False, {
			"error": jsonbp.errorType.VALUE_PARSING,
			"context": {}
		}

	sanedStrValue = (sanedValue
		.replace(separator, '')
		.replace(decimalMark, '.')
	)

	precision = f"1e-{specs['precision']}"
	rawValue = Decimal(sanedStrValue).quantize(Decimal(precision),
		context=roundingContext)

	if specs['min'] > rawValue or rawValue > specs['max']:
		return False, {
			"error": jsonbp.errorType.OUTSIDE_RANGE,
			"context": { "value": rawValue }
		}

	return True, rawValue


type_specs = {
	'name': 'decimal',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}

