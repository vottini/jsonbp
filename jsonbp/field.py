
class JsonField:
	def __init__(self, fieldKind, fieldType):
		self.fieldKind = fieldKind
		self.fieldType = fieldType
		self.optional = False
		self.nullable = False

	def setOptional(self): self.optional = True
	def setNullable(self): self.nullable = True

#-------------------------------------------------------------------------------

def createField(fieldKind, fieldType):
	return JsonField(fieldKind, fieldType)

