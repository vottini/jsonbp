
import re
import json
import uuid

from . import field_type
from . import error_type

from .types import primitive_types
from .exception import SerializationException
from .error import createErrorForField, createErrorForNode, createErrorForRoot
from .array import isArray

#-------------------------------------------------------------------------------

class JsonBlueprint:
	def __init__(self):
		self.uuid = uuid.uuid4()
		self.includes = list()
		self.derived_types = dict()
		self.enums = dict()
		self.nodes = dict()
		self.root = None

	def __str__(self):
		return (
			f"blueprint: {self.uuid}\n" +
			f"|-> types = {self.derived_types}\n" +
			f"|-> enums = {self.enums}\n" +
			f"|-> nodes = {self.nodes}\n" +
			f"'-> root = {self.root}")

	#-----------------------------------------------------------------------------

	def deserialize_field(self, fieldName, fieldType, value):
		if fieldType in primitive_types:
			specs = primitive_types[fieldType]['defaults']
			baseType = fieldType

		else:
			specs = self.find_element_declaration(fieldType)
			baseType = specs['__baseType__']

		try:
			deserialize_method = primitive_types[baseType]['parser']
			success, outcome = deserialize_method(value, specs)

			if not success:
				return False, createErrorForField(fieldName,
					outcome["error"], type=baseType,
					**outcome["context"])

			return success, outcome

		except Exception as e:
			return False, createErrorForField(fieldName,
				error_type.VALUE_PARSING, type=baseType)


	def validate_enum(self, fieldName, enumType, value):
		if None == value:
			return False, createErrorForField(fieldName,
				error_type.NULL_VALUE)

		if not isinstance(value, str):
			return False, createErrorForField(fieldName,
				error_type.INVALID_ENUM, value=value)

		possibleValues = self.find_enum_declaration(enumType)

		if not value in possibleValues:
			return False, createErrorForField(fieldName, 
				error_type.UNKNOWN_LITERAL, value=value)
		
		return True, value


	def validate_array(self, fieldName, jArray, contents):
		if not isinstance(contents, list):
			return False, createErrorForField(fieldName,
				error_type.INVALID_ARRAY)

		arrayLen = len(contents)
		if not jArray.minLength <= arrayLen <= jArray.maxLength:
			return False, createErrorForField(fieldName,
				error_type.INVALID_LENGTH, length=arrayLen)

		arrayKind = jArray.fieldKind
		arrayType = jArray.fieldType

		if arrayKind == field_type.NODE:
			arrayNode = self.find_node_declaration(arrayType)
			for idx, content in enumerate(contents):
				success, processed = self.validate_node(fieldName, arrayNode, content)

				if not success:
					processed.setAsArrayElement(idx)
					return False, processed

				contents[idx] = processed

			return True, contents

		if arrayKind == field_type.ENUM:
			for idx, value in enumerate(contents):
				success, processed = self.validate_enum(fieldName, arrayType, value)

				if not success:
					processed.setAsArrayElement(idx)
					return False, processed

				contents[idx] = processed

			return True, contents

		for idx, value in enumerate(contents):
			success, processed = self.deserialize_field(fieldName, arrayType, value)

			if not success:
				processed.setAsArrayElement(idx)
				return False, processed

			contents[idx] = processed

		return True, contents


	def validate_node(self, nodeName, node, contents):
		if not isinstance(contents, dict):
			return False, createErrorForNode(nodeName,
				error_type.INVALID_NODE)

		for fieldName, fieldData in node.items():
			if not fieldName in contents:
				if fieldData.optional: continue
				return False, createErrorForNode(nodeName,
					error_type.MISSING_FIELD, field=fieldName)

			retrieved = contents[fieldName]
			if isArray(fieldData):
				success, processed = self.validate_array(fieldName, fieldData, retrieved)
				if success: continue
				return success, processed

			fieldKind = fieldData.fieldKind
			fieldType = fieldData.fieldType

			if fieldKind == field_type.NODE:
				nodeSpecs = self.find_node_declaration(fieldType)
				success, processed = self.validate_node(fieldName, nodeSpecs, retrieved)
				if not success: return success, processed
				contents[fieldName] = processed
				continue

			if fieldKind == field_type.ENUM:
				success, processed = self.validate_enum(fieldName, fieldType, retrieved)
				if not success: return success, processed
				contents[fieldName] = processed
				continue

			success, processed = self.deserialize_field(fieldName, fieldType, retrieved)
			if not success: return False, processed
			contents[fieldName] = processed

		return True, contents


	def validate(self, rootContents):
		if isArray(self.root):
			return self.validate_array(None, self.root, rootContents)

		rootKind = self.root.fieldKind
		rootType = self.root.fieldType

		if rootKind == field_type.NODE:
			rootNode = self.find_node_declaration(rootType)
			return self.validate_node(None, rootNode, rootContents)

		if rootKind == field_type.ENUM:
			rootEnum = self.find_enum_declaration(rootType)
			return self.validate_enum(None, rootType, rootContents)

		if rootKind == field_type.SIMPLE:
			return self.deserialize_field(None, rootType, rootContents)


	def deserialize(self, contents):
		identity = lambda x : x

		try:
			loaded = json.loads(contents,
				parse_float=identity, parse_int=identity,
				parse_constant=identity)

		except json.JSONDecodeError as e:
			return False, createErrorForRoot(error_type.JSON_PARSING,
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
			collected.extend(source.derived_types.keys())
			collected.extend(source.enums.keys())
			collected.extend(source.nodes.keys())

		return collected


	def __hash__(self):
		return hash(self.uuid)

	#----------------------------------------------------------------------------

	def find_element_declaration(self, typeName, checked=None):
		if typeName in primitive_types: return primitive_types[typeName]['defaults']
		if typeName in self.derived_types: return self.derived_types[typeName]
		checked = checked or set()
		checked.add(self)

		for blueprint in self.includes:
			if not blueprint in checked:
				found = blueprint.find_element_declaration(typeName, checked)
				if None != found: return found
		
		return None
	
	
	def find_node_declaration(self, nodeName, checked=None):
		if nodeName in self.nodes: return self.nodes[nodeName]
		checked = checked or set()
		checked.add(self)
	
		for blueprint in self.includes:
			if not blueprint in checked:
				found = blueprint.find_node_declaration(nodeName, checked)
				if None != found: return found
	
		return None
	
	
	def find_enum_declaration(self, enumName, checked=None):
		if enumName in self.enums: return self.enums[enumName]
		checked = checked or set()
		checked.add(self)
	
		for blueprint in self.includes:
			if not blueprint in checked:
				found = blueprint.find_enum_declaration(enumName, checked)
				if None != found: return found

		return None

	#----------------------------------------------------------------------------

	def chooseRoot(self, rootName):
		pass

	#----------------------------------------------------------------------------

	def serialize_element(self, element, elementName, content):
		contentKind = element.fieldKind
		contentType = element.fieldType

		method = {
			field_type.NODE: JsonBlueprint.serialize_node,
			field_type.ENUM: JsonBlueprint.serialize_enum,
			field_type.SIMPLE: JsonBlueprint.serialize_field
		} [contentKind]

		if isArray(element):
			try: iterator = iter(content)

			except TypeError:
				content_type = type(content)
				msg = f"{elementName}: Array content cannot be extracted from '{content_type}' value"
				raise SerializationException(msg)

			serialized = list()
			for idx, item in enumerate(content):
				idxName = f"{elementName} index {idx}"
				processed = method(self, contentType, idxName, item)
				serialized.append(processed)

			inner = ",".join(serialized)
			return f"[{inner}]"

		return method(self, contentType, elementName, content)


	def serialize_node(self, nodeType, nodeName, content):
		node = self.find_node_declaration(nodeType)

		if not isinstance(content, dict):
			msg = f"{nodeName} needs to receive a dict to serialize"
			raise SerializationException(msg)

		serialized = list()
		for fieldName, fieldData in node.items():
			if not fieldName in content:
				if fieldData.optional: continue
				msg = f"{nodeName}: missing field {fieldName}"
				raise SerializationException(msg)

			fieldValue = content[fieldName]
			processed = self.serialize_element(fieldData, fieldName, fieldValue)
			serialized.append(f'"{fieldName}":{processed}')

		inner = ",".join(serialized)
		return f"{{{inner}}}"


	def serialize_enum(self, enumType, fieldName, content):
		possibleValues = self.find_enum_declaration(enumType)

		if not content in possibleValues:
			msg = f"Value '{value}' is not valid for field '{fieldName}'"
			raise SerializationException(msg)

		return f'"{content}"'


	def serialize_field(self, fieldType, fieldName, content):
		if fieldType in primitive_types:
			specs = primitive_types[fieldType]['defaults']
			baseType = fieldType

		else:
			specs = self.find_element_declaration(fieldType)
			baseType = specs['__baseType__']

		serialize_method = primitive_types[baseType]['formatter']  #globals()['s_' + baseType]
		return serialize_method(content, specs)

	#-------------------------------------------------------------------------------

	def serialize(self, content):
		return self.serialize_element(self.root, "Root Level", content)

