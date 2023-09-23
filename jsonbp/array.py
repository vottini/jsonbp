
from sys import maxsize
from .exception import SchemaViolation
from .field import JsonField

_array_specs = [
	"minLength",
	"maxLength",
	"nullableArray"
]

def checkedInt(value):
	if type(value) is not int: raise Exception(f"Bad integer: {value}")
	return value

class JsonArray(JsonField):
	def __init__(self, baseField):
		JsonField.__init__(self,
			baseField.fieldKind,
			baseField.fieldType)

		self.nullable = baseField.nullable
		self.nullableArray = False
		self.maxLength = maxsize
		self.minLength = 0


	def applySpec(self, spec, value):
		if not spec in _array_specs:
			msg = f"Invalid array spec '{spec}'"
			raise SchemaViolation(msg)

		try:
			if "minLength" == spec: self.minLength = checkedInt(value)
			if "maxLength" == spec: self.maxLength = checkedInt(value)

			if "nullableArray" == spec:
				if value in (True, False):
					self.nullableArray = value

				else:
					msg = f"Bad boolean: {value}"
					raise Exception(msg)

		except Exception:
			msg = f"Invalid value for array spec '{spec}': {value}"
			raise SchemaViolation(msg)

		if not (0 <= self.minLength <= self.maxLength and 0 < self.maxLength):
			msg = f"Invalid array length for '{spec}'"
			raise SchemaViolation(msg)

#------------------------------------------------------------------------------

def makeArray(baseField):
	return JsonArray(baseField)

def isArray(decl):
	return isinstance(decl, JsonArray)

