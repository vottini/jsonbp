
import configparser
from . import errorType

_error_names = ([ entry
	for entry in dir(errorType)
	if not entry.startswith('_')
])

_error_codes = dict()
for error_name in _error_names:
	error_code = getattr(errorType, error_name)
	_error_codes[error_name] = error_code

#-------------------------------------------------------------------------------

fallbackLanguage = "en_US"
possiblePrefixes = {'FIELD', 'OBJECT', 'ARRAY', 'ROOT'}
translations = dict()

defaultLanguage = "en_US"
def useDefaultLanguage(language):
	global defaultLanguage
	defaultLanguage = language

#-------------------------------------------------------------------------------

def loadTranslation(filename, language):

	try:
		with open(filename) as fd:
			contents = fd.read()

	except IOError as e:
		printWarning(f"Unable to read localization file: {e.strerror}")
		return

	translation = translations.get(language, dict())
	translations[language] = translation

	config = configparser.ConfigParser()
	config.read_string(contents)
	sections = config.sections()

	if 'Messages' in sections:
		messages = translation.get('messages', dict())
		translation['messages'] = messages

		section = config['Messages']
		for entry in config.options('Messages'):
			sanedEntry = entry.upper()

			if sanedEntry in _error_codes:
				index = _error_codes[sanedEntry]
				messages[index] = section[sanedEntry]

	if 'Prefixes' in sections:
		prefixes = translation.get('prefixes', dict())
		translation['prefixes'] = prefixes

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

	def format(self, localizationPriority=None):
		localizationPriority = (localizationPriority
			if localizationPriority is not None
			else [defaultLanguage])

		for candidate in localizationPriority:
			translation = translations.get(candidate)
			if translation is not None:
				break

		else:
			translation = translations[fallbackLanguage]

		prefix = translation["prefixes"][self.prefix]
		prefixText = prefix.format(assignee=self.assignee,
			index=self.index)

		message = translation["messages"][self.error_id]
		messageText = message.format(**self.context)
		return ": ".join([prefixText, messageText])

	def __str__(self):
		return self.format()

#-------------------------------------------------------------------------------

def createErrorForField(fieldName, error_id, **context):
	result = _instance(error_id, **context)
	args = ("FIELD", fieldName) if fieldName != None else ("ROOT",)
	result.setAssignee(*args)
	return result


def createErrorForObject(objectName, error_id, **context):
	result = _instance(error_id, **context)
	args = ("OBJECT", objectName) if objectName != None else ("ROOT",)
	result.setAssignee(*args)
	return result


def createErrorForRoot(error_id, **context):
	result = _instance(error_id, **context)
	result.setAssignee("ROOT")
	return result

#-------------------------------------------------------------------------------

from sys import stderr

def printWarning(message):
	print(f"\033[92m[Warning]\033[00m {message}",
		file=stderr)

def printError(message):
	print(f"\033[91m[Error]\033[00m {message}",
		file=stderr)

#-------------------------------------------------------------------------------

__all__ = [
	"loadTranslation",
	"useDefaultLanguage",
	"createErrorForField",
	"createErrorForObject",
	"createErrorForRoot"
]

