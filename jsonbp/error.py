
import configparser
from . import error_type

_error_names = ([ entry
	for entry in dir(error_type)
	if not entry.startswith('_')
])

_error_codes = dict()
for error_name in _error_names:
	error_code = getattr(error_type, error_name)
	_error_codes[error_name] = error_code

#-------------------------------------------------------------------------------

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

	config = configparser.ConfigParser()
	config.read_string(contents)
	sections = config.sections()

	if 'Messages' in sections:
		section = config['Messages']
		for entry in config.options('Messages'):
			sanedEntry = entry.upper()

			if sanedEntry in _error_codes:
				index = _error_codes[sanedEntry]
				texts[index] = section[sanedEntry]

	if 'Prefixes' in sections:
		section = config['Prefixes']
		for entry in config.options('Prefixes'):
			sanedEntry = entry.upper()

			if sanedEntry in possiblePrefixes:
				prefixValue = section[sanedEntry]
				prefixes[sanedEntry] = prefixValue

#-------------------------------------------------------------------------------

class _instance:
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

def createErrorForField(fieldName, error_id, **context):
	result = _instance(error_id, **context)
	args = ("FIELD", fieldName) if fieldName != None else ("ROOT",)
	result.setAssignee(*args)
	return result


def createErrorForNode(nodeName, error_id, **context):
	result = _instance(error_id, **context)
	args = ("NODE", nodeName) if nodeName != None else ("ROOT",)
	result.setAssignee(*args)
	return result


def createErrorForRoot(error_id, **context):
	result = _instance(error_id, **context)
	result.setAssignee("ROOT")
	return result

#-------------------------------------------------------------------------------

__all__ = [
	"useTranslation",
	"createErrorForField",
	"createErrorForNode",
	"createErrorForRoot"
]

