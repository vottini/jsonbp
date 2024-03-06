
import re
import json
import uuid
import collections.abc

from . import fieldKind
from . import errorType

from .field import createField
from .exception import SchemaViolation, SerializationException
from .error import createErrorForField, createErrorForNode, createErrorForRoot
from .array import makeArray, isArray
from .unquoted import unquotedStr

#-------------------------------------------------------------------------------

# as taken from
# https://stackoverflow.com/a/62395407/21680913

def noBoolConvert(pairs):
	return { key: unquotedStr(str(value).lower())
		if isinstance(value, bool) else value
		for key, value in pairs
	}

#-------------------------------------------------------------------------------

class JsonBlueprint:
	def __init__(self, primitiveTypes):
		self.primitiveTypes = primitiveTypes
		self.uuid = uuid.uuid4()
		self.includes = list()
		self.derivedTypes = dict()
		self.enums = dict()
		self.objects = dict()
		self.root = None

	def __str__(self):
		return (
			f"blueprint: {self.uuid}\n" +
			f"|-> primitive types = {self.primitiveTypes}\n" +
			f"|-> derived types = {self.derivedTypes}\n" +
			f"|-> enums = {self.enums}\n" +
			f"|-> objects = {self.objects}\n" +
			f"'-> root = {self.root}")

	#-----------------------------------------------------------------------------

	def deserializeField(self, fieldName, fieldType, value):
		if fieldType in self.primitiveTypes:
			specs = self.primitiveTypes[fieldType]['defaults']
			baseType = fieldType

		else:
			specs = self.findElementDeclaration(fieldType)
			baseType = specs['__baseType__']

		try:
			deserializeMethod = self.primitiveTypes[baseType]['parser']
			success, outcome = deserializeMethod(value, specs)

			if not success:
				return False, createErrorForField(fieldName,
					outcome["error"], type=baseType,
					**outcome["context"])

			return success, outcome

		except Exception as e:
			return False, createErrorForField(fieldName,
				errorType.VALUE_PARSING, type=baseType)


	def validateEnum(self, fieldName, enumType, value):
		if isinstance(value, unquotedStr):
			return False, createErrorForField(fieldName,
				errorType.INVALID_ENUM, value=value)

		possibleValues = self.findEnumDeclaration(enumType)

		if not value in possibleValues:
			return False, createErrorForField(fieldName,
				errorType.UNKNOWN_LITERAL, value=value)

		return True, value


	def validateArray(self, fieldName, jArray, contents):
		if not isinstance(contents, collections.abc.Sequence):
			return False, createErrorForField(fieldName,
				errorType.INVALID_ARRAY)

		arrayLen = len(contents)
		if not jArray.minLength <= arrayLen <= jArray.maxLength:
			return False, createErrorForField(fieldName,
				errorType.INVALID_LENGTH, length=arrayLen)

		arrayKind = jArray.fieldKind
		arrayType = jArray.fieldType

		elementType = arrayType
		deserializer = (self.validateEnum
			if arrayKind == fieldKind.ENUM
			else self.deserializeField)

		if arrayKind == fieldKind.OBJECT:
			elementType = self.findNodeDeclaration(arrayType)
			deserializer = self.validateNode

		for idx, value in enumerate(contents):
			if value is None:
				if jArray.nullable:
					contents[idx] = None
					continue

				return False, createErrorForNode(fieldName,
					errorType.NULL_VALUE, field=fieldName)

			success, processed = deserializer(fieldName, elementType, value)

			if not success:
				processed.setAsArrayElement(idx)
				return False, processed

			contents[idx] = processed

		return True, contents


	def validateNode(self, objectName, objectInstance, contents):
		if not isinstance(contents, collections.abc.Mapping):
			return False, createErrorForNode(objectName,
				errorType.INVALID_OBJECT)

		for fieldName, fieldData in objectInstance.items():
			if not fieldName in contents:
				if fieldData.optional: continue
				return False, createErrorForNode(objectName,
					errorType.MISSING_FIELD, field=fieldName)

			retrieved = contents[fieldName]

			if isArray(fieldData):
				if retrieved is None:
					if fieldData.nullableArray:
						contents[fieldName] = None
						continue

					else:
						return False, createErrorForNode(objectName,
							errorType.NULL_VALUE, field=fieldName)

				success, processed = self.validateArray(fieldName, fieldData, retrieved)
				if not success: return False, processed
				continue

			if retrieved is None:
				if fieldData.nullable:
					contents[fieldName] = None
					continue

				return False, createErrorForNode(objectName,
					errorType.NULL_VALUE, field=fieldName)

			kind = fieldData.fieldKind
			fieldType = fieldData.fieldType

			if kind == fieldKind.OBJECT:
				objectSpecs = self.findNodeDeclaration(fieldType)
				success, processed = self.validateNode(fieldName, objectSpecs, retrieved)
				if not success: return False, processed
				contents[fieldName] = processed
				continue

			if kind == fieldKind.ENUM:
				success, processed = self.validateEnum(fieldName, fieldType, retrieved)
				if not success: return False, processed
				contents[fieldName] = processed
				continue

			success, processed = self.deserializeField(fieldName, fieldType, retrieved)
			if not success: return False, processed
			contents[fieldName] = processed

		return True, contents


	def validate(self, rootContents):
		if isArray(self.root):
			if rootContents is not None:
				return self.validateArray(None, self.root,
					rootContents)

				if self.root.nullableArray:
					return True, None

				else:
					return False, createErrorForNode(None,
						errorType.NULL_VALUE, field="root")

		if None == rootContents:
			if self.root.nullable:
				return True, None

			else:
				return False, createErrorForNode(None,
					errorType.NULL_VALUE, field="root")

		rootKind = self.root.fieldKind
		rootType = self.root.fieldType

		if rootKind == fieldKind.OBJECT:
			rootNode = self.findNodeDeclaration(rootType)
			return self.validateNode(None, rootNode,
				rootContents)

		if rootKind == fieldKind.ENUM:
			rootEnum = self.findEnumDeclaration(rootType)
			return self.validateEnum(None, rootType,
				rootContents)

		if rootKind == fieldKind.SIMPLE:
			return self.deserializeField(None, rootType,
				rootContents)


	def deserialize(self, contents):
		if self.root is None:
			msg = "No root defined for blueprint, unable to deserialize"
			raise SchemaViolation(msg)

		try:
			identity = lambda x : x
			unquote = lambda x : unquotedStr(x)

			loaded = json.loads(contents,
				object_pairs_hook=noBoolConvert,
				parse_float=unquote, parse_int=unquote,
				parse_constant=identity)

		except json.JSONDecodeError as e:
			return False, createErrorForRoot(errorType.JSON_PARSING,
				line=e.lineno, column=e.colno, message=e.msg)

		return self.validate(loaded)

	#----------------------------------------------------------------------------

	def collectSources(self, collected=None):
		collected = collected if None != collected else set()
		collected.add(self)

		for blueprint in self.includes:
			blueprint.collectSources(collected)

		return collected


	def collectTypes(self):
		collected = list()
		sources = self.collectSources()

		for source in sources:
			collected.extend(source.derivedTypes.keys())
			collected.extend(source.enums.keys())
			collected.extend(source.objects.keys())

		return collected


	def __hash__(self):
		return hash(self.uuid)

	#----------------------------------------------------------------------------

	def findElementDeclaration(self, typeName, checked=None):
		if typeName in self.primitiveTypes: return self.primitiveTypes[typeName]['defaults']
		if typeName in self.derivedTypes: return self.derivedTypes[typeName]
		checked = checked or set()
		checked.add(self)

		for blueprint in self.includes:
			if not blueprint in checked:
				found = blueprint.findElementDeclaration(typeName, checked)
				if None != found: return found

		return None


	def findNodeDeclaration(self, objectName, checked=None):
		if objectName in self.objects: return self.objects[objectName]
		checked = checked or set()
		checked.add(self)

		for blueprint in self.includes:
			if not blueprint in checked:
				found = blueprint.findNodeDeclaration(objectName, checked)
				if None != found: return found

		return None


	def findEnumDeclaration(self, enumName, checked=None):
		if enumName in self.enums: return self.enums[enumName]
		checked = checked or set()
		checked.add(self)

		for blueprint in self.includes:
			if not blueprint in checked:
				found = blueprint.findEnumDeclaration(enumName, checked)
				if None != found: return found

		return None

	#----------------------------------------------------------------------------

	def chooseRoot(self, rootType, asArray=False,
		minArrayLength=None, maxArrayLength=None):

		lookups = [
			(self.findNodeDeclaration, fieldKind.OBJECT),
			(self.findElementDeclaration, fieldKind.SIMPLE),
			(self.findEnumDeclaration, fieldKind.ENUM)
		]

		foundRoot = None
		rootKind = None

		for method, kind in lookups:
			if candidate := method(rootType, set()):
				foundRoot = candidate
				rootKind = kind
				break

		if foundRoot is None:
			msg = f"No element found with name '{rootType}'"
			raise SchemaViolation(msg)

		rootField = createField(rootKind, rootType)
		newBp = JsonBlueprint(self.primitiveTypes)
		newBp.root = (makeArray(rootField) if asArray else
			rootField)

		if asArray:
			if minArrayLength: newBp.root.applySpec('minLength', minArrayLength)
			if maxArrayLength: newBp.root.applySpec('maxLength', maxArrayLength)

		newBp.includes = self.includes
		newBp.derivedTypes = self.derivedTypes
		newBp.enums = self.enums
		newBp.objects = self.objects

		return newBp

	#----------------------------------------------------------------------------

	def serializeElement(self, element, elementName, content):
		contentKind = element.fieldKind
		contentType = element.fieldType

		method = {
			fieldKind.OBJECT: JsonBlueprint.serializeNode,
			fieldKind.ENUM: JsonBlueprint.serializeEnum,
			fieldKind.SIMPLE: JsonBlueprint.serializeField
		} [contentKind]

		if isArray(element):
			if content is None:
				if element.nullableArray: return 'null'
				msg = f"{elementName}: Array cannot be null"
				raise SerializationException(msg)

			try: iterator = iter(content)

			except TypeError:
				content_type = type(content)
				raise SerializationException(
					f"{elementName}: Array content cannot be extracted "
					f"from '{content_type}' value"
				)

			serialized = list()
			for idx, item in enumerate(content):
				if item is None:
					if element.nullable:
						serialized.append('null')
						continue

					else:
						msg = f"{elementName} is not nullable"
						raise SerializationException(msg)

				idxName = f"{elementName} index {idx}"
				processed = method(self, contentType, idxName, item)
				serialized.append(processed)

			inner = ",".join(serialized)
			return f"[{inner}]"

		if content is None:
			if element.nullable: return 'null'
			msg = f"{elementName} is not nullable"
			raise SerializationException(msg)

		return method(self, contentType, elementName, content)


	def serializeNode(self, objectType, objectName, content):
		objectInstance = self.findNodeDeclaration(objectType)

		if not isinstance(content, collections.abc.Mapping):
			msg = f"{objectName} needs to receive a dict to serialize"
			raise SerializationException(msg)

		serialized = list()
		for fieldName, fieldData in objectInstance.items():
			if not fieldName in content:
				if fieldData.optional:
					continue

				msg = f"{objectName}: missing field {fieldName}"
				raise SerializationException(msg)

			fieldValue = content[fieldName]
			processed = self.serializeElement(fieldData, fieldName, fieldValue)
			serialized.append(f'"{fieldName}":{processed}')

		inner = ",".join(serialized)
		return f"{{{inner}}}"


	def serializeEnum(self, enumType, fieldName, content):
		possibleValues = self.findEnumDeclaration(enumType)

		if not content in possibleValues:
			msg = f"Value '{content}' is not valid for field '{fieldName}'"
			raise SerializationException(msg)

		return f'"{content}"'


	def serializeField(self, fieldType, fieldName, content):
		if fieldType in self.primitiveTypes:
			specs = self.primitiveTypes[fieldType]['defaults']
			baseType = fieldType

		else:
			specs = self.findElementDeclaration(fieldType)
			baseType = specs['__baseType__']

		serialize_method = self.primitiveTypes[baseType]['formatter']
		return serialize_method(content, specs)

	#-------------------------------------------------------------------------------

	def serialize(self, content):
		if self.root is None:
			msg = "No root defined for blueprint, unable to serialize"
			raise SerializationException(msg)

		if content is None:
			if self.root.nullable:
				return 'null'

		return self.serializeElement(self.root,
			"Root Level", content)

