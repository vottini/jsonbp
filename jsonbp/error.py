
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

possible_prefixes = {
	'FIELD',
	'OBJECT',
	'ARRAY',
	'ROOT'
}

fallback_language = "en_US"
default_language = "en_US"
translations = dict()

def use_default_language(language):
	"""Defines which language to use to map errors by default.

		This language will be applied when no languages are
		specified in the :func:`DeserializationError.localize` method. When
		jsonbp starts, this language is set to American English (en-US). If 
		he language code passed is not available, it'll also fallback to
		American English.

		Args:
			language (str): Language code to set

		Returns:
			Nothing

	"""

	global default_language
	default_language = language

#-------------------------------------------------------------------------------

def load_translation(filename, language):

	"""Includes languages to be used in deserialization issues localization.

		This function appends or overwrites languages available for use
		in the method :func:`DeserializationError.localize`. jsonbp comes
		with some builtin translations already, check its source if unsure.

		Args:
			filename (str): path to the ini file.
			language (str): language code that that file corresponds to.

		Raises:
			IOError: When `filename` cannot be opened for reading.

		Returns:
			Nothing

	"""

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

class DeserializationError:
	"""Error returned from failed deserializations."""

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

	def localize(self, localization_priority=None):
		"""Maps the error to possible localizations.

			Args:
				localization_priority ([str]): list of locale codes,
					in order of priority, to attempt to localize the issue.
					If no list is passed, it will use the language defined by
					:func:`use_default_language`.

			Returns:
				the localized issue with the JSON string.
				
		"""

		localization_priority = (localization_priority
			if localization_priority is not None
			else [default_language])

		for candidate in localization_priority:
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
		return self.localize()

#-------------------------------------------------------------------------------

def create_field_error(fieldName, error_id, **context):
	result = DeserializationError(error_id, **context)
	args = ("FIELD", fieldName) if fieldName != None else ("ROOT",)
	result.set_assignee(*args)
	return result


def create_object_error(objectName, error_id, **context):
	result = DeserializationError(error_id, **context)
	args = ("OBJECT", objectName) if objectName != None else ("ROOT",)
	result.set_assignee(*args)
	return result


def create_root_error(error_id, **context):
	result = DeserializationError(error_id, **context)
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
	"DeserializationError",
	"create_field_error",
	"create_object_error",
	"create_root_error"
]

