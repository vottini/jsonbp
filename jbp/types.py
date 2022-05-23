
from decimal import Decimal

bytesLength = 4
maxBits = (bytesLength * 8)
signalizedMaxBits = maxBits - 1
greatest = (1 << signalizedMaxBits) - 1
lowest = -(1 << signalizedMaxBits)

print("GREATEST", greatest)
print("LOWEST", lowest)

primitive_types = {
	'integer' : {
		'min': lowest,
		'max': greatest
	},

	'float' : {
		'min': float('-inf'),
		'max': float('+inf')
	},

	'decimal' : {
		'fractionalLength': 2,
		'min': Decimal(-lowest).quantize(Decimal('0.01')),
		'max': Decimal(+greatest).quantize(Decimal('0.01')),
		'decimalSeparator': '.',
		'groupSeparator': ''
	},

	'bool' : {
		'coerce': False
	},

	'datetime' : {
		'format': "%Y-%m-%d %H:%M:%S"
	},

	'string': {
		'minLength': 0,
		'maxLength': 1024
	},
}

