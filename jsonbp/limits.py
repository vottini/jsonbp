
bytesLength = 4
maxBits = (bytesLength * 8)
signalizedMaxBits = maxBits - 1
greatestNumber = (1 << signalizedMaxBits) - 1
lowestNumber = -(1 << signalizedMaxBits)

#from decimal import Decimal
#import re

#primitive_types = {
#	'integer' : {
#		'min': lowest,
#		'max': greatest
#	},
#
#	'float' : {
#		'atLeast': float('-inf'),
#		'atMost': float('+inf'),
#		'greaterThan': float('-inf'),
#		'lessThan': float('+inf')
#	},
#
#	'decimal' : {
#		'fractionalLength': 2,
#		'min': Decimal(lowest).quantize(Decimal('0.01')),
#		'max': Decimal(greatest).quantize(Decimal('0.01')),
#		'decimalSeparator': '.',
#		'groupSeparator': ''
#	},
#
#	'bool' : {
#		'coerce': False
#	},
#
#	'datetime' : {
#		'format': "%Y-%m-%dT%H:%M:%S.%f%z"
#	},
#
#	'string': {
#		'minLength': 0,
#		'maxLength': 1024,
#		'format': re.compile(r"^[^$]*$")
#	},
#}

