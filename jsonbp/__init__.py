
import os

from .parser import load, loads, invalidateCache
from .jbp import violation as jbpViolation
from .jbp import error as jbpError

SchemaViolation = jbpViolation.JsonViolation

def useLanguage(languageCode):
	localizationPath = f'messages.{languageCode}.ini'

	if not os.path.isfile(localizationPath):
		localizationPath = os.path.join(
			os.path.dirname(__file__),
			"localization",
			localizationPath)

	jbpError.useTranslation(localizationPath)


defaultLanguage = "en_US"
useLanguage(defaultLanguage)

__all__ = [
	"load",
	"loads",
	"invalidateCache",
	"SchemaViolation",
	"useLanguage"
]

