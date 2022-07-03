
class TypeDeclaration:
	def __init__(self, typeName, specs):
		self.typeName = typeName
		self.specs = specs

	def isCustomized(self):
		return len(self.specs) > 0

#-------------------------------------------------------------------------------

def create(typeName, specs):
	return TypeDeclaration(typeName, specs)

