
import os

from .types import unquoted_str, ErrorType
from .parser import load_file, load_string, invalidate_cache
from .exception import SchemaViolation, SerializationException
from .error import load_translation, use_default_language

jsonbp_path = os.path.dirname(__file__)
localizationPath = os.path.join(jsonbp_path, "localization")
for filename in os.listdir(localizationPath):
	if not filename.endswith('.ini'): # pragma: no cover
		continue

	translation, ini = filename.split('.')
	fullPath = os.path.join(localizationPath, filename)
	load_translation(fullPath, translation)

__all__ = [
	"load_file",
	"load_string",
	"use_default_language",
	"invalidate_cache",
	"SchemaViolation",
	"SerializationException"
]

