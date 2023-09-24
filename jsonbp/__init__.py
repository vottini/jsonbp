
import os

from . import errorType
from .parser import loadFile, loadString, invalidateCache
from .exception import SchemaViolation, SerializationException
from .error import useTranslation
from .unquoted import unquotedStr

def useLanguage(languageCode):
	localizationPath = f'messages.{languageCode}.ini'

	if not os.path.isfile(localizationPath):
		localizationPath = os.path.join(
			os.path.dirname(__file__),
			"localization",
			localizationPath)

	useTranslation(localizationPath)


defaultLanguage = "en_US"
useLanguage(defaultLanguage)

__all__ = [
	"loadFile",
	"loadString",
	"invalidateCache",
	"SchemaViolation",
	"useLanguage"
]

