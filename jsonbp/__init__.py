
import os

from . import error_type
from .parser import load, loads, invalidateCache
from .exception import SchemaViolation
from .error import useTranslation

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
	"load",
	"loads",
	"invalidateCache",
	"SchemaViolation",
	"useLanguage"
]

