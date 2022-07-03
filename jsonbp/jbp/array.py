
from sys import maxsize
from . import violation as jbpViolation
from . import field as jbpField

class JsonArray(jbpField.JsonField):
	def __init__(self, baseField):
		jbpField.JsonField.__init__(self,
			baseField.fieldKind,
			baseField.fieldType)

		self.maxLength = maxsize
		self.minLength = 0


	def applySpec(self, spec, value):
		if not spec in ("minLength", "maxLength"):
			msg = f"Invalid array spec '{spec}'"
			raise jbpViolation.JsonViolation(msg)

		if value < 0:
			msg = f"Invalid array length: {value}"
			raise jbpViolation.JsonViolation(msg)

		if "minLength" == spec: self.minLength = value
		if "maxLength" == spec: self.maxLength = value

		if not (0 <= self.minLength <= self.maxLength and 0 < self.maxLength):
			msg = f"Invalid array length for '{spec}'"
			raise jbpViolation.JsonViolation(msg)

#------------------------------------------------------------------------------

def makeArray(baseField):
	return JsonArray(baseField)

def isArray(decl):
	return isinstance(decl, JsonArray)

