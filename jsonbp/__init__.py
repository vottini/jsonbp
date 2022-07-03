
import os
import os.path

from . import parser
from .jbp import violation as jbpViolation
from .jbp import error as jbpError


load = parser.load
loads = parser.loads
SchemaViolation = jbpViolation.JsonViolation


def useLanguage(languageCode):
	localizationPath = f'messages.{languageCode}.ini'

	if not os.path.isfile(localizationPath):
		scriptPath = os.path.dirname(__file__)
		localizationPath = f'{scriptPath}/localization/messages.{languageCode}.ini'

	#print(f"Using file {localizationPath}")
	jbpError.useTranslation(localizationPath)


defaultLanguage = "en_US"
useLanguage(defaultLanguage)
