
import re
import json
import uuid
import collections.abc

from .field import create_field
from .types import ErrorType, FieldType, unquoted_str
from .exception import SchemaViolation, SerializationException
from .error import create_field_error, create_object_error, create_root_error
from .array import make_array, is_array

#-------------------------------------------------------------------------------

# as taken from
# https://stackoverflow.com/a/62395407/21680913

def no_bool_converter(pairs):
	return { key: unquoted_str(str(value).lower())
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

	def __str__(self): # pragma: no cover
		return (
			f"blueprint: {self.uuid}\n" +
			f"|-> primitive types = {self.primitiveTypes}\n" +
			f"|-> derived types = {self.derivedTypes}\n" +
			f"|-> enums = {self.enums}\n" +
			f"|-> objects = {self.objects}\n" +
			f"'-> root = {self.root}")

	#-----------------------------------------------------------------------------

	def _deserialize_field(self, fieldName, fieldType, value):
		if fieldType in self.primitiveTypes:
			specs = self.primitiveTypes[fieldType]['defaults']
			baseType = fieldType

		else:
			specs = self._find_element_decl(fieldType)
			baseType = specs['__baseType__']

		try:
			deserializeMethod = self.primitiveTypes[baseType]['parser']
			success, outcome = deserializeMethod(value, specs)

			if not success:
				return False, create_field_error(fieldName,
					outcome["error"], type=baseType,
					**outcome["context"])

			return success, outcome

		except Exception as e:
			return False, create_field_error(fieldName,
				ErrorType.VALUE_PARSING, type=baseType)


	def _validate_enum(self, fieldName, enumType, value):
		if isinstance(value, unquoted_str):
			return False, create_field_error(fieldName,
				ErrorType.INVALID_ENUM, value=value)

		possibleValues = self._find_enum_decl(enumType)

		if not value in possibleValues:
			return False, create_field_error(fieldName,
				ErrorType.UNKNOWN_LITERAL, value=value)

		return True, value


	def _validate_array(self, fieldName, jArray, contents):
		if not isinstance(contents, collections.abc.Sequence):
			return False, create_field_error(fieldName,
				ErrorType.INVALID_ARRAY)

		arrayLen = len(contents)
		if not jArray.minLength <= arrayLen <= jArray.maxLength:
			return False, create_field_error(fieldName,
				ErrorType.INVALID_LENGTH, length=arrayLen)

		arrayKind = jArray.fieldKind
		arrayType = jArray.fieldType

		elementType = arrayType
		deserializer = (self._validate_enum
			if arrayKind == FieldType.ENUM
			else self._deserialize_field)

		if arrayKind == FieldType.OBJECT:
			elementType = self._find_object_decl(arrayType)
			deserializer = self._validate_object

		for idx, value in enumerate(contents):
			if value is None:
				if jArray.nullable:
					contents[idx] = None
					continue

				return False, create_object_error(fieldName,
					ErrorType.NULL_VALUE, field=fieldName)

			success, processed = deserializer(fieldName, elementType, value)

			if not success:
				processed.set_as_array_index(idx)
				return False, processed

			contents[idx] = processed

		return True, contents


	def _validate_object(self, objectName, objectInstance, contents):
		if not isinstance(contents, collections.abc.Mapping):
			return False, create_object_error(objectName,
				ErrorType.INVALID_OBJECT)

		for fieldName, fieldData in objectInstance.items():
			if not fieldName in contents:
				if fieldData.optional: continue
				return False, create_object_error(objectName,
					ErrorType.MISSING_FIELD, field=fieldName)

			retrieved = contents[fieldName]

			if is_array(fieldData):
				if retrieved is None:
					if fieldData.nullableArray:
						contents[fieldName] = None
						continue

					else:
						return False, create_object_error(objectName,
							ErrorType.NULL_VALUE, field=fieldName)

				success, processed = self._validate_array(fieldName, fieldData, retrieved)
				if not success: return False, processed
				continue

			if retrieved is None:
				if fieldData.nullable:
					contents[fieldName] = None
					continue

				return False, create_object_error(objectName,
					ErrorType.NULL_VALUE, field=fieldName)

			kind = fieldData.fieldKind
			fieldType = fieldData.fieldType

			if kind == FieldType.OBJECT:
				objectSpecs = self._find_object_decl(fieldType)
				success, processed = self._validate_object(fieldName, objectSpecs, retrieved)
				if not success: return False, processed
				contents[fieldName] = processed
				continue

			if kind == FieldType.ENUM:
				success, processed = self._validate_enum(fieldName, fieldType, retrieved)
				if not success: return False, processed
				contents[fieldName] = processed
				continue

			success, processed = self._deserialize_field(fieldName, fieldType, retrieved)
			if not success: return False, processed
			contents[fieldName] = processed

		return True, contents


	def validate(self, rootContents):
		if is_array(self.root):
			if rootContents is not None:
				return self._validate_array(None, self.root,
					rootContents)

				if self.root.nullableArray:
					return True, None

				else:
					return False, create_object_error(None,
						ErrorType.NULL_VALUE, field="root")

		if None == rootContents:
			if self.root.nullable:
				return True, None

			else:
				return False, create_object_error(None,
					ErrorType.NULL_VALUE, field="root")

		rootKind = self.root.fieldKind
		rootType = self.root.fieldType

		if rootKind == FieldType.OBJECT:
			rootObject = self._find_object_decl(rootType)
			return self._validate_object(None, rootObject,
				rootContents)

		if rootKind == FieldType.ENUM:
			rootEnum = self._find_enum_decl(rootType)
			return self._validate_enum(None, rootType,
				rootContents)

		if rootKind == FieldType.SIMPLE:
			return self._deserialize_field(None, rootType,
				rootContents)


	def deserialize(self, contents):
		if self.root is None:
			msg = "No root defined for blueprint, unable to deserialize"
			raise SchemaViolation(msg)

		try:
			identity = lambda x : x
			unquote = lambda x : unquoted_str(x)

			loaded = json.loads(contents,
				object_pairs_hook=no_bool_converter,
				parse_float=unquote, parse_int=unquote,
				parse_constant=identity)

		except json.JSONDecodeError as e:
			return False, create_root_error(ErrorType.JSON_PARSING,
				line=e.lineno, column=e.colno, message=e.msg)

		return self.validate(loaded)

	#----------------------------------------------------------------------------

	def _collect_sources(self, collected=None):
		collected = collected if None != collected else set()
		collected.add(self)

		for blueprint in self.includes:
			blueprint._collect_sources(collected)

		return collected


	def _collect_types(self):
		collected = list()
		sources = self._collect_sources()

		for source in sources:
			collected.extend(source.derivedTypes.keys())
			collected.extend(source.enums.keys())
			collected.extend(source.objects.keys())

		return collected


	def __hash__(self):
		return hash(self.uuid)

	#----------------------------------------------------------------------------

	def _find_element_decl(self, typeName, checked=None):
		if typeName in self.primitiveTypes: return self.primitiveTypes[typeName]['defaults']
		if typeName in self.derivedTypes: return self.derivedTypes[typeName]
		checked = checked or set()
		checked.add(self)

		for blueprint in self.includes:
			if not blueprint in checked:
				found = blueprint._find_element_decl(typeName, checked)
				if None != found: return found

		return None


	def _find_object_decl(self, objectName, checked=None):
		if objectName in self.objects: return self.objects[objectName]
		checked = checked or set()
		checked.add(self)

		for blueprint in self.includes:
			if not blueprint in checked:
				found = blueprint._find_object_decl(objectName, checked)
				if None != found: return found

		return None


	def _find_enum_decl(self, enumName, checked=None):
		if enumName in self.enums:
			return self.enums[enumName]

		checked = checked or set()
		checked.add(self)

		for blueprint in self.includes:
			if not blueprint in checked:
				found = blueprint._find_enum_decl(enumName, checked)
				if None != found: return found

		return None

	#----------------------------------------------------------------------------

	def choose_root(self, rootType, asArray=False,
		minArrayLength=None, maxArrayLength=None):

		lookups = [
			(self._find_object_decl, FieldType.OBJECT),
			(self._find_element_decl, FieldType.SIMPLE),
			(self._find_enum_decl, FieldType.ENUM)
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

		rootField = create_field(rootKind, rootType)
		newBp = JsonBlueprint(self.primitiveTypes)
		newBp.root = (make_array(rootField) if asArray else
			rootField)

		if asArray:
			if minArrayLength: newBp.root.apply_spec('minLength', minArrayLength)
			if maxArrayLength: newBp.root.apply_spec('maxLength', maxArrayLength)

		newBp.includes = self.includes
		newBp.derivedTypes = self.derivedTypes
		newBp.enums = self.enums
		newBp.objects = self.objects

		return newBp

	#----------------------------------------------------------------------------

	def _serialize_element(self, element, elementName, content):
		contentKind = element.fieldKind
		contentType = element.fieldType

		method = {
			FieldType.OBJECT: JsonBlueprint._serialize_object,
			FieldType.ENUM: JsonBlueprint._serialize_enum,
			FieldType.SIMPLE: JsonBlueprint._serialize_field
		} [contentKind]

		if is_array(element):
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


	def _serialize_object(self, objectType, objectName, content):
		objectInstance = self._find_object_decl(objectType)

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
			processed = self._serialize_element(fieldData, fieldName, fieldValue)
			serialized.append(f'"{fieldName}":{processed}')

		inner = ",".join(serialized)
		return f"{{{inner}}}"


	def _serialize_enum(self, enumType, fieldName, content):
		possibleValues = self._find_enum_decl(enumType)

		if not content in possibleValues:
			msg = f"Value '{content}' is not valid for field '{fieldName}'"
			raise SerializationException(msg)

		return f'"{content}"'


	def _serialize_field(self, fieldType, fieldName, content):
		if fieldType in self.primitiveTypes:
			specs = self.primitiveTypes[fieldType]['defaults']
			baseType = fieldType

		else:
			specs = self._find_element_decl(fieldType)
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

		return self._serialize_element(self.root,
			"Root Level", content)

