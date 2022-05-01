
import re
import decimal
import json

import jbp.error as jbpError
import jbp.field as jbpField
import jbp.array as jbpArray

from decimal import Decimal
from datetime import datetime
from jbp.types import primitive_types

#-------------------------------------------------------------------------------

class taggedNumber:
	def __init__(self, strValue): self.strValue = strValue
	def __str__(self): return self.strValue
	__repr__ =  __str__

#-------------------------------------------------------------------------------

def d_integer(fieldName, value, specs):
	strValue = value.strValue if isinstance(value, taggedNumber) else value

	if None == value:
		return False, jbpError.createForField(fieldName,
			jbpError.NULL_VALUE)

	try:
		rawValue = int(strValue)
		if not specs['min'] <= rawValue <= specs['max']:
			return False, jbpError.createForField(fieldName,
				jbpError.OUTSIDE_RANGE, value=rawValue)

	except Exception as e:
		return False, jbpError.createForField(fieldName,
			jbpError.INTEGER_PARSING, text=strValue)

	return True, rawValue


def d_float(fieldName, value, specs):
	strValue = value.strValue if isinstance(value, taggedNumber) else value

	if None == value:
		return False, jbpError.createForField(fieldName,
			jbpError.NULL_VALUE)

	try:
		sanedValue = strValue.replace('Infinity', 'inf')
		rawValue = float(sanedValue)

		if not specs['min'] <= rawValue <= specs['max']:
			return False, jbpError.createForField(fieldName,
				jbpError.OUTSIDE_RANGE, value=rawValue)

	except Exception as e:
		return False, jbpError.createForField(fieldName,
			jbpError.FLOAT_PARSING, text=strValue)

	return True, rawValue


roundingContext = decimal.Context(rounding=decimal.ROUND_DOWN)
specialChars = r'.^$*+?|'

def d_fixed(fieldName, value, specs):
	strValue = value.strValue if isinstance(value, taggedNumber) else value

	if None == strValue:
		return False, jbpError.createForField(fieldName,
			jbpError.NULL_VALUE)

	if not isinstance(strValue, str):
		return False, jbpError.createForField(fieldName,
			jbpError.FIXED_PARSING, text=strValue)

	grpSep = specs['groupSeparator']
	decSep = specs['decimalSeparator']

	if grpSep in specialChars: grpSep = f'\\{grpSep}'
	if decSep in specialChars: decSep = f'\\{decSep}'
	fixedPattern = f'^[+-]?\\d+({grpSep}\\d+)*({decSep}\\d+)?$'

	if None == re.match(fixedPattern, strValue):
		return False, jbpError.createForField(fieldName,
			jbpError.FIXED_PARSING, text=strValue)

	try:
		precision = f"1e-{specs['fractionalLength']}"
		sanedStrValue = strValue.replace(specs['groupSeparator'], '')
		sanedStrValue = sanedStrValue.replace(specs['decimalSeparator'], '.')
		rawValue = Decimal(sanedStrValue).quantize(Decimal(precision),
			context=roundingContext)

		if specs['min'] > rawValue or rawValue > specs['max']:
			return False, jbpError.createForField(fieldName,
				jbpError.OUTSIDE_RANGE, value=rawValue)

	except Exception as e:
		return False, jbpError.createForField(fieldName,
			jbpError.FIXED_PARSING, text=strValue)

	return True, rawValue


def d_bool(fieldName, value, specs):
	value = value.strValue if isinstance(value, taggedNumber) else value

	if isinstance(value, bool):
		return True, value

	if not specs['coerce']:
		return False, jbpError.createForField(fieldName,
			jbpError.INVALID_BOOLEAN, value=value)

	# coercion attempt
	# check if is 'null' or empty string
	if None == value or 0 == len(value):
		return True, False

	try:
		rawValue = float(value)
		# check if is effectively zero or NaN
		if 0 == rawValue or rawValue != rawValue:
			return True, False

	except Exception as e:
		# it was just an attempt, no problem
		pass

	# if none of the above, then most likely it's a truthy value
	return True, True


def d_datetime(fieldName, value, specs):
	strValue = value.strValue if isinstance(value, taggedNumber) else value

	try:
		parsed_date = datetime.strptime(strValue, specs['format'])
		return True, parsed_date

	except Exception as e:
		return False, jbpError.createForField(fieldName,
			jbpError.INVALID_DATETIME, text=strValue)


def d_string(fieldName, strValue, specs):
	if not isinstance(strValue, str):
		return False, jbpError.createForField(fieldName,
			jbpError.INVALID_STRING, value=strValue)

	strLength = len(strValue)
	if not specs['minLength'] <= strLength <= specs['maxLength']:
		return False, jbpError.createForField(fieldName,
			jbpError.INVALID_LENGTH, length=strLength)

	return True, strValue

#-------------------------------------------------------------------------------

class JsonBlueprint:
	def __init__(self, root, derived_types, nodes, enums):
		self.root = root
		self.derived_types = derived_types
		self.nodes = nodes
		self.enums = enums

	def __str__(self):
		return (f'types = {self.derived_types} '
			+ f'enums = {self.enums} '
			+ f'nodes = {self.nodes} '
			+ f'root = {self.root}')


	def deserialize_field(self, fieldName, fieldType, value):
		if fieldType in primitive_types:
			specs = primitive_types[fieldType]
			baseType = fieldType

		else:
			specs = self.derived_types[fieldType]
			baseType = specs['__baseType__']

		deserialize_method = globals()['d_' + baseType]
		return deserialize_method(fieldName, value, specs)


	def validate_enum(self, fieldName, value, enumType):
		if None == value:
			return False, jbpError.createForField(fieldName,
				jbpError.NULL_VALUE)

		if not isinstance(value, str):
			return False, jbpError.createForField(fieldName,
				jbpError.INVALID_ENUM, value=value)

		possibleValues = self.enums[enumType]
		if not value in possibleValues:
			return False, jbpError.createForField(fieldName, 
				jbpError.UNKNOWN_LITERAL, value=value)
		
		return True, value


	def validate_array(self, fieldName, jArray, contents):
		if not isinstance(contents, list):
			return False, jbpError.createForField(fieldName,
				jbpError.INVALID_ARRAY)

		arrayLen = len(contents)
		if not jArray.minLength <= arrayLen <= jArray.maxLength:
			return False, jbpError.createForField(fieldName,
				jbpError.INVALID_LENGTH, length=arrayLen)

		arrayKind = jArray.fieldKind
		arrayType = jArray.fieldType

		if arrayKind == jbpField.NODE:
			arrayNode = self.nodes[arrayType]
			for idx, content in enumerate(contents):
				success, processed = self.validate_node(fieldName, arrayNode, content)

				if not success:
					processed.setAsArrayElement(idx)
					return False, processed

				contents[idx] = processed

			return True, contents

		if arrayKind == jbpField.ENUM:
			for idx, value in enumerate(contents):
				success, processed = self.validate_enum(fieldName, value, arrayType)

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
			return False, jbpError.createForNode(nodeName,
				jbpError.INVALID_NODE)

		for fieldName, fieldData in node.items():
			if not fieldName in contents:
				if fieldData.optional: continue
				return False, jbpError.createForNode(nodeName,
					jbpError.MISSING_FIELD, field=fieldName)

			retrieved = contents[fieldName]
			if jbpArray.isArray(fieldData):
				success, processed = self.validate_array(fieldName, fieldData, retrieved)
				if not success: return success, processed
				continue

			fieldKind = fieldData.fieldKind
			fieldType = fieldData.fieldType

			if fieldKind == jbpField.NODE:
				nodeSpecs = self.nodes[fieldType]
				success, processed = self.validate_node(fieldName, nodeSpecs, retrieved)
				if not success: return success, processed
				contents[fieldName] = processed
				continue

			if fieldKind == jbpField.ENUM:
				success, processed = self.validate_enum(fieldName, retrieved, fieldType)
				if not success: return success, processed
				contents[fieldName] = processed
				continue

			success, processed = self.deserialize_field(fieldName, fieldType, retrieved)
			if not success: return False, processed
			contents[fieldName] = processed

		return True, contents


	def validate(self, rootContents):
		if jbpArray.isArray(self.root):
			return self.validate_array(None, self.root, rootContents)

		rootKind = self.root.fieldKind
		rootType = self.root.fieldType

		if rootKind == jbpField.NODE:
			rootNode = self.nodes[rootType]
			return self.validate_node(None, rootNode, rootContents)

		if rootKind == jbpField.ENUM:
			rootEnum = self.enums[rootType]
			return self.validate_enum(None, rootNode, rootContents)

		if rootKind == jbpField.SIMPLE:
			return self.deserialize_field(None, rootType, rootContents)
			pass


	def deserialize(self, contents):
		tag_number = lambda x : taggedNumber(x)
		ident = lambda x : x

		try:
			loaded = json.loads(contents,
				parse_float=tag_number, parse_int=tag_number,
				parse_constant=ident)

		except json.JSONDecodeError as e:
			return False, jbpError.createForRoot(jbpError.JSON_PARSING,
				line=e.lineno, column=e.colno, message=e.msg)
	
		return self.validate(loaded)

