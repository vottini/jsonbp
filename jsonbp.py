
import ply.lex as lex
import ply.yacc as yacc

import jbp.error as jbpError
import jbp.array as jbpArray
import jbp.declaration as jbpDeclaration

reserved = (
	'root',
	'node',
	'type',
	'enum',
	'optional',
	'extends'
)

literals = (
	'{',
	'}',
	'(',
	')',
	'[',
	']',
	',',
	'=',
	':'
)

# List of tokens

types = (
	'STRING',
	'BOOLEAN',
	'FLOAT_AMOUNT',
	'INTEGER_AMOUNT',
	'IDENTIFIER',
)

tokens = list(types) + [token.upper() for token in reserved]

#------------------------------------------------------------

def t_STRING(t):
	r'"[^"]*"'
	t.value = t.value[1:-1]
	return t

def t_BOOLEAN(t):
	r'true|false'
	t.value = (t.value == 'true')
	return t

def t_FLOAT_AMOUNT(t):
	r'[-+]?\d+(\.(\d+)?([eE][-+]?\d+)?|[eE][-+]?\d+)'
	t.value = float(t.value)
	return t

def t_INTEGER_AMOUNT(t):
	r'[+-]?\d+'
	t.value = int(t.value)
	return t

def t_IDENTIFIER(t):
	r'\w+'

	identifier = t.value
	if identifier in reserved:
		t.type = identifier.upper()

	return t

#----------------------------------------------------------------

def t_newline(t):
	r'\n+'
	t.lexer.lineno += len(t.value)

def t_comment(t):
	r'[#][^\n]*'
	pass

t_ignore  = ' \t\r'

#---------------------------------------------------------------

from sys import maxsize
from datetime import datetime
from decimal import Decimal

import decimal
import re

primitive_types = {
	'integer' : {
		'min': -maxsize,
		'max': +maxsize
	},

	'float' : {
		'min': float('-inf'),
		'max': float('+inf')
	},

	'fixed' : {
		'fractionalLength': 2,
		'min': Decimal(-maxsize).quantize(Decimal('0.01')),
		'max': Decimal(+maxsize).quantize(Decimal('0.01')),
		'decimalSeparator': '.',
		'groupSeparator': ''
	},

	'bool' : {
		'coerce': False
	},

	'datetime' : {
		'format': "%Y-%m-%d %H:%M:%S"
	},

	'string': {
		'minLength': 0,
		'maxLength': 1024
	},
}

#---------------------------------------------------------------

class taggedNumber:
	def __init__(self, strValue): self.strValue = strValue
	def __str__(self): return self.strValue
	__repr__ =  __str__

#---------------------------------------------------------------

class TokenException(Exception): pass
class ParseException(Exception): pass

def t_error(t):
	msg = f"Illegal character '{t.value[0]}' on line {t.lineno}"
	raise TokenException(msg)

def p_error(p):
	if p == None: raise ParseException("Empty blueprint")
	msg = f"Syntax error in line {p.lineno}: token '{p.value}' misplaced"
	raise ParseException(msg)

#---------------------------------------------------------------

def initGlobals():
	global derived_types
	global enums
	global nodes
	global root

	derived_types = dict()
	enums = dict()
	nodes = dict()
	root = None

#---------------- general structure -----------------------------

def p_schema(p):
	'''
	    schema : schema construction
						 | construction
	'''

def p_construction(p):
	'''
	    construction : type
					         | enum
									 | node
									 | root
	'''

#---------------- constructs -----------------------------

def p_root(p):
	'''
	    root : ROOT node_declaration

	'''

	global root
	if None != root:
		msg = 'Only one root can be defined'
		raise ParseException(msg)

	root = p[2]
	p[0] = root


def p_node(p):
	'''
		node : NODE IDENTIFIER EXTENDS IDENTIFIER node_declaration
		     | NODE IDENTIFIER node_declaration
	'''

	if len(p) == 6:
		base_node = p[4]
		if not base_node in nodes:
			msg = f"Node '{base_node}' is not defined"
			raise ParseException(msg)

		base_decls = nodes[base_node]
		extended_decls = p[5]
		own_name = p[2]

		for fieldName, fieldDeclaration in extended_decls.items():
			if fieldName in base_decls:
				msg = f"Field '{fieldName}' in node '{own_name}' is already defined in base node '{base_node}'"
				raise ParseException(msg)

		extended_decls.update(base_decls)
		nodes[own_name] = extended_decls

	else:
		own_name = p[2]
		extended_decls = p[3]
		nodes[own_name] = extended_decls


def p_node_specs(p):
	'''
		node_declaration : '{' attributes '}'
	'''

	decls = p[2]
	new_node = dict()
	for decl in decls:
		new_node[decl[0]] = decl[1]

	p[0] = new_node


def create_type(decl):
	origin = (
		primitive_types[decl.kind]
			if decl.kind in primitive_types
			else derived_types[decl.kind])

	new_kind = dict()
	for attrib, value in origin.items():
		new_kind[attrib] = value

	for specificity in decl.specs:
		attrib, value = specificity
		if not attrib in new_kind:
			msg = f"Type '{decl.name}' ({decl.kind}) has no attribute {attrib}"
			raise ParseException(msg)

		oldValue = new_kind[attrib]
		if type(oldValue) == Decimal and type(value) == float: value = Decimal(value)
		if type(oldValue) == float and type(value) == int: value = float(value)

		if type(value) != type(oldValue):
			msg = f"New value for specificity '{attrib}' is {type(value).__name__}, but it expects {type(oldValue).__name__}"
			raise ParseException(msg)

		new_kind[attrib] = value

	base_type = decl.kind
	while not base_type in primitive_types:
		parent_type = derived_types[base_type]
		base_type = parent_type['__baseType__']

	new_kind['__baseType__'] = base_type
	return new_kind


def p_type(p):
	'''
			type : TYPE IDENTIFIER ':' element_declaration
	'''

	decl = p[4]
	new_kind = create_type(decl)
	derived_types[p[2]] = new_kind


#---------------- attributes ----------------------------

def p_attributes(p):
	'''
		attributes : attributes ',' attribute
		           | attribute
	'''

	if len(p) == 4: p[1].append(p[3])
	if len(p) == 2: p[1] = [p[1]]
	p[0] = p[1]


def p_attribute(p):
	'''
		attribute : OPTIONAL attribution
		          | attribution
	'''

	if len(p) == 3:
		p[2][1].setOptional()
		p[0] = p[2]

	else:
		p[0] = p[1]


def p_attribution(p):
	'''
		attribution : IDENTIFIER ':' array_declaration
		            | IDENTIFIER ':' local_declaration
	'''

	p[0] = (p[1], p[3])


def p_array_declaration(p):
	'''
		array_declaration : local_declaration '[' specificities ']'
		                  | local_declaration '[' ']'
	'''

	jArray = jbpArray.makeArray(p[1])
	
	if len(p) == 5:
		for specificity in p[3]:
			spec, value = specificity
			jArray.applySpec(spec, value)

	p[0] = jArray


def p_local_declaration(p):
	'''
		local_declaration : element_declaration
	'''
	
	decl = p[1]
	if len(decl.specs) > 0:
		new_kind = create_type(decl)
		adhoc_type = '_anonymous_' + str(len(derived_types)) + '_'
		derived_types[adhoc_type] = new_kind
		decl.kind = adhoc_type

	p[0] = decl


def p_element_declaration(p):
	'''
		element_declaration : IDENTIFIER '(' specificities ')'
		                    | IDENTIFIER
	'''

	kind = p[1]
	kind_exists = (
		kind in primitive_types or
		kind in derived_types or
		kind in enums or
		kind in nodes)
	
	if not kind_exists:
		msg = f"Unknown type '{kind}'"
		raise ParseException(msg)

	specs = p[3] if len(p) == 5 else list()
	p[0] = jbpDeclaration.create(kind, specs)


def p_specificities(p):
	'''
		specificities : specificities ',' specificity
		              | specificity
	'''

	if len(p) == 4: p[1].append(p[3])
	if len(p) == 2: p[1] = [p[1]]
	p[0] = p[1]


def p_specificity(p):
	'''
	    specificity : IDENTIFIER '=' specified_value
	'''

	p[0] = (p[1], p[3])


def p_specified_value(p):
	'''
	    specified_value : STRING
	                    | FLOAT_AMOUNT
	                    | INTEGER_AMOUNT
	                    | BOOLEAN
	'''

	p[0] = p[1]

#---------------- enums -----------------------------

def p_enum(p):
	'''
			enum : ENUM IDENTIFIER '{' constants '}'
	'''

	enums[p[2]] = p[4]
	p[0] = 0


def p_constants(p):
	'''
			constants : constants ',' IDENTIFIER
								| IDENTIFIER
	'''

	if len(p) == 4:
		p[1].append(p[3])
		p[0] = p[1]
	
	else:
		p[0] = [p[1]]

#---------------------------------------------------------------

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

#---------------------------------------------------------------

import json

class blueprint:
	def __init__(self):
		self.root = root
		self.derived_types = derived_types
		self.nodes = nodes
		self.enums = enums

	def __str__(self):
		return (f'types = {self.derived_types} '
			+ f'enums = {self.enums} '
			+ f'nodes = {self.nodes} '
			+ f'root = {self.root}')


	def deserialize_field(self, attrib, decl, retrieved):
		if decl.kind in primitive_types:
			specs = primitive_types[decl.kind]
			baseType = decl.kind

		else:
			specs = self.derived_types[decl.kind]
			baseType = specs['__baseType__']

		deserialize_method = globals()['d_' + baseType]
		return deserialize_method(attrib, retrieved, specs)


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

		decl = jArray.content
		if decl.kind in self.nodes:
			arrayNode = self.nodes[decl.kind]

			for idx, content in enumerate(contents):
				success, result = self.validate_node(decl.kind, arrayNode, content)

				if not success:
					result.setAsArrayElement(idx)
					return False, result

			return True, decl

		if decl.kind in self.enums:
			for idx, value in enumerate(contents):
				success, processed = self.validate_enum(fieldName, value, decl.kind)

				if not success:
					processed.setAsArrayElement(idx)
					return False, processed

			return True, decl

		for idx, value in enumerate(contents):
			success, processed = self.deserialize_field(fieldName, decl, value)

			if not success:
				processed.setAsArrayElement(idx)
				return False, processed

			contents[idx] = processed

		return True, contents


	def validate_node(self, nodeName, node, contents):
		if not isinstance(contents, dict):
			return False, jbpError.createForNode(nodeName,
				jbpError.INVALID_NODE)

		for fieldName, decl in node.items():
			if not fieldName in contents:
				if decl.optional: continue
				return False, jbpError.createForNode(nodeName,
					jbpError.MISSING_FIELD, field=fieldName)

			retrieved = contents[fieldName]
			if jbpArray.isArray(decl):
				success, processed = self.validate_array(fieldName, decl, retrieved)
				if not success: return success, processed
				continue

			attr_type = decl.kind
			if attr_type in self.nodes:
				node_decl = self.nodes[attr_type]
				success, processed = self.validate_node(attr_type, node_decl, retrieved)
				if not success: return success, processed
				continue

			if attr_type in self.enums:
				success, processed = self.validate_enum(fieldName, retrieved, attr_type)
				if not success: return success, processed
				continue

			success, processed = self.deserialize_field(fieldName, decl, retrieved)
			if not success: return False, processed
			contents[fieldName] = processed

		return True, contents


	def validate(self, root_contents):
		return self.validate_node(None, self.root, root_contents)


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

#-------------------------------------------------------------------------------

from threading import Lock
mutex = Lock()

def load(filename):
	with open(filename, "r") as fd:
		contents = fd.read()
		return loads(contents)

lexer = lex.lex()
parser = yacc.yacc()

def loads(contents):
	with mutex:
		initGlobals()
		parser.parse(contents)
		result = blueprint()
		return result

