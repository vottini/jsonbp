
class declaration:
	def __init__(self, kind, specs):
		self.kind = kind
		self.specs = specs
		self.optional = False

	def setOptional(self):
		self.optional = True

	def __str__(self):
		return f"{self.kind} -> {self.specs}"

#-------------------------------------------------------------------------------

def create(kind, specs):
	return declaration(kind, specs)

