
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
	'radix': '.',
	'separator': '',
	'indianFormat': False,
	'prefix': "",
	'suffix': ""
}


roundingContext = decimal.Context(rounding=decimal.ROUND_DOWN)
specialChars = r'.^$*+?|'

def _format(value, specs):
	radix = specs['radix']
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
	content = (radix.join([integerPart, decimalPart])
		if len(parts) > 1
		else integerPart)

	parts = ([ part
		for part in [ specs['prefix'], content, specs['suffix'] ]
		if len(part) > 0
	])

	needsQuotes = (
		len(parts) > 1 or
		'.' != radix or
		'' != separator)

	formattedParts = "".join(parts)
	return (f'"{formattedParts}"' if needsQuotes
		else formattedParts)


def _parse(value, specs):
	try:
		sanedValue = (value
			.removeprefix(specs['prefix'])
			.removesuffix(specs['suffix'])
		)

		radix = specs['radix']
		if radix in specialChars:
			radix = f'\\{radix}'

		separator = specs['separator']
		if separator in specialChars:
			separator = f'\\{separator}'

		decimalPattern = f'^[+-]?\\d+({separator}\\d+)*({radix}\\d+)?$'
		if None == re.match(decimalPattern, sanedValue):
			print(f"{value} => ERROR PARSING DECIMAL = DOESN'T MATCH")
			return False, {
				"error": jsonbp.ErrorType.VALUE_PARSING,
				"context": {}
			}

		sanedStrValue = (sanedValue
			.replace(specs['separator'], '')
			.replace(specs['radix'], '.')
		)

		precision = f"1e-{specs['precision']}"
		rawValue = Decimal(sanedStrValue).quantize(Decimal(precision),
			context=roundingContext)

		if specs['min'] > rawValue or rawValue > specs['max']:
			return False, {
				"error": jsonbp.ErrorType.OUTSIDE_RANGE,
				"context": { "value": rawValue }
			}

		return True, rawValue

	except Exception as e:
		print(f"{value} => ERROR PARSING DECIMAL", repr(e))
		return False, {
			"error": jsonbp.ErrorType.VALUE_PARSING,
			"context": {"type": "decimal"}
		}


type_specs = {
	'name': 'decimal',
	'parser': _parse,
	'formatter': _format,
	'defaults': _defaults
}

