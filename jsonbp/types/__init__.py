
from . import integer
from . import float
from . import decimal
from . import bool
from . import instant
from . import string

type_specs = [
	integer.type_specs,
	float.type_specs,
	decimal.type_specs,
	bool.type_specs,
	instant.type_specs,
	string.type_specs
]

primitive_types = dict()
for type_spec in type_specs:
	name = type_spec['name']
	primitive_types[name] = type_spec

