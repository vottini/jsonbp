
import os

from . import errorType
from .parser import loadFile, loadString, invalidateCache
from .exception import SchemaViolation, SerializationException
from .error import loadTranslation, useDefaultLanguage
from .unquoted import unquotedStr

jsonbpPath = os.path.dirname(__file__)
localizationPath = os.path.join(jsonbpPath, "localization")
for filename in os.listdir(localizationPath):
	if not filename.endswith('.ini'): # pragma: no cover
		continue

	translation, ini = filename.split('.')
	fullPath = os.path.join(localizationPath, filename)
	loadTranslation(fullPath, translation)

__all__ = [
	"loadFile",
	"loadString",
	"useDefaultLanguage",
	"invalidateCache",
	"SchemaViolation"
]

