
# kinds

SIMPLE = 0
ENUM   = 1
NODE   = 2

class JsonField:
	def __init__(self, fieldKind, fieldType):
		self.fieldKind = fieldKind
		self.fieldType = fieldType
		self.optional = False

	def setOptional(self):
		self.optional = True

#-------------------------------------------------------------------------------

def create(fieldKind, fieldType):
	return JsonField(fieldKind, fieldType)

