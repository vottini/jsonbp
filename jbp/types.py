
from sys import maxsize
from decimal import Decimal

primitive_types = {
	'integer' : {
		'min': -maxsize,
		'max': +maxsize
	},

	'float' : {
		'min': float('-inf'),
		'max': float('+inf')
	},

	'decimal' : {
		'fractionalLength': 2,
		'min': Decimal(-maxsize).quantize(Decimal('0.01')),
		'max': Decimal(+maxsize).quantize(Decimal('0.01')),
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

