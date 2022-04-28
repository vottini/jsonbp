
from sys import maxsize
from jbp.violation import BlueprintViolation

class JsonArray:
	def __init__(self, content):
		self.content = content
		self.maxLength = maxsize
		self.minLength = 0


	def applySpec(self, spec, value):
		if spec in ("minLength", "maxLength"):

			if value < 0:
				msg = f"Invalid array length: {value}"
				raise BlueprintViolation(msg)

			if "minLength" == spec: self.minLength = value
			if "maxLength" == spec: self.maxLength = value
			return
			
		msg = f"Invalid array spec '{spec}'"
		raise BlueprintViolation(msg)

#------------------------------------------------------------------------------

def makeArray(content): return JsonArray(content)
def isArray(decl): return isinstance(decl, JsonArray)

