
import configparser
from .types import ErrorType

_error_names = ([ entry
	for entry in dir(ErrorType)
	if not entry.startswith('_')
])

_error_codes = dict()
for error_name in _error_names:
	error_code = getattr(ErrorType, error_name)
	_error_codes[error_name] = error_code

#-------------------------------------------------------------------------------

fallback_language = "en_US"
possible_prefixes = {'FIELD', 'OBJECT', 'ARRAY', 'ROOT'}
translations = dict()

default_language = "en_US"
def use_default_language(language):
	global default_language
	default_language = language

#-------------------------------------------------------------------------------

def load_translation(filename, language):

	try:
		with open(filename) as fd:
			contents = fd.read()

	except IOError as e:
		print_warning(f"Unable to read localization file: {e.strerror}")
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

			if sanedEntry in possible_prefixes:
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

	def error_type(self):
		return self.error_id

	def set_assignee(self, assigneeType, assigneeName=None):
		self.prefix = assigneeType
		self.assignee = assigneeName

	def set_as_array_index(self, arrayIndex):
		self.prefix = "ARRAY"
		self.index = arrayIndex

	def format(self, localizationPriority=None):
		localizationPriority = (localizationPriority
			if localizationPriority is not None
			else [default_language])

		for candidate in localizationPriority:
			translation = translations.get(candidate)
			if translation is not None:
				break

		else:
			translation = translations[fallback_language]

		prefix = translation["prefixes"][self.prefix]
		prefixText = prefix.format(assignee=self.assignee,
			index=self.index)

		message = translation["messages"][self.error_id]
		messageText = message.format(**self.context)
		return ": ".join([prefixText, messageText])

	def __str__(self):
		return self.format()

#-------------------------------------------------------------------------------

def create_field_error(fieldName, error_id, **context):
	result = _instance(error_id, **context)
	args = ("FIELD", fieldName) if fieldName != None else ("ROOT",)
	result.set_assignee(*args)
	return result


def create_object_error(objectName, error_id, **context):
	result = _instance(error_id, **context)
	args = ("OBJECT", objectName) if objectName != None else ("ROOT",)
	result.set_assignee(*args)
	return result


def create_root_error(error_id, **context):
	result = _instance(error_id, **context)
	result.set_assignee("ROOT")
	return result

#-------------------------------------------------------------------------------

from sys import stderr

def print_warning(message):
	print(f"\033[92m[Warning]\033[00m {message}",
		file=stderr)

def print_error(message):
	print(f"\033[91m[Error]\033[00m {message}",
		file=stderr)

#-------------------------------------------------------------------------------

__all__ = [
	"load_translation",
	"use_default_language",
	"create_field_error",
	"create_object_error",
	"create_root_error"
]

