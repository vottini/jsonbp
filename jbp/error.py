
import configparser

JSON_PARSING     = 0    # line, column, message
NULL_VALUE       = 1    # 
INTEGER_PARSING  = 2    # text
FLOAT_PARSING    = 3    # text
DECIMAL_PARSING  = 4    # text
OUTSIDE_RANGE    = 5    # value
INVALID_BOOLEAN  = 6    # value
INVALID_STRING   = 7    # value
INVALID_LENGTH   = 8    # length
INVALID_DATETIME = 9    # text
UNKNOWN_LITERAL  = 10   # text
INVALID_ENUM     = 11   # value
MISSING_FIELD    = 12   # field
INVALID_ARRAY    = 13   # 
INVALID_NODE     = 14   # 

texts = dict()
possiblePrefixes = {'FIELD', 'NODE', 'ARRAY', 'ROOT'}
prefixes = dict()

#-------------------------------------------------------------------------------

def useTranslation(filename):

	try:
		with open(filename) as fd:
			contents = fd.read()

	except IOError as e:
		print(f"Unable to read localization file: {e.strerror}")
		return

	entries = globals()
	config = configparser.ConfigParser()
	config.read_string(contents)
	sections = config.sections()

	if 'Messages' in sections:
		section = config['Messages']
		for entry in config.options('Messages'):
			sanedEntry = entry.upper()

			if sanedEntry in entries:
				index = entries[sanedEntry]
				texts[index] = section[sanedEntry]

	if 'Prefixes' in sections:
		section = config['Prefixes']
		for entry in config.options('Prefixes'):
			sanedEntry = entry.upper()

			if sanedEntry in possiblePrefixes:
				prefixValue = section[sanedEntry]
				prefixes[sanedEntry] = prefixValue

#-------------------------------------------------------------------------------

class instance:
	def __init__(self, error_id, **context):
		self.error_id = error_id
		self.context = context
		self.prefix = None
		self.assignee = None
		self.index = None

	def getErrorType(self):
		return self.error_id

	def setAssignee(self, assigneeType, assigneeName=None):
		self.prefix = assigneeType
		self.assignee = assigneeName

	def setAsArrayElement(self, arrayIndex):
		self.prefix = "ARRAY"
		self.index = arrayIndex

	def __str__(self):
		prefixText = ""
		if None != self.prefix:
			prefix = prefixes[self.prefix]
			prefixText = prefix.format(
				assignee=self.assignee,
				index=self.index)

		msg = texts[self.error_id]
		errorMsg = msg.format(**self.context)
		return " ".join([prefixText, errorMsg])

#-------------------------------------------------------------------------------

def createForField(fieldName, error_id, **context):
	result = instance(error_id, **context)
	args = ("FIELD", fieldName) if fieldName != None else ("ROOT",)
	result.setAssignee(*args)
	return result


def createForNode(nodeName, error_id, **context):
	result = instance(error_id, **context)
	args = ("NODE", nodeName) if nodeName != None else ("ROOT",)
	result.setAssignee(*args)
	return result


def createForRoot(error_id, **context):
	result = instance(error_id, **context)
	result.setAssignee("ROOT")
	return result

