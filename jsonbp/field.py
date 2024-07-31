
class JsonField:
	def __init__(self, fieldKind, fieldType):
		self.fieldKind = fieldKind
		self.fieldType = fieldType
		self.optional = False
		self.nullable = False

#-------------------------------------------------------------------------------

def create_field(fieldKind, fieldType):
	return JsonField(fieldKind, fieldType)

