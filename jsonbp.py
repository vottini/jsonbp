
import ply.lex as lex
import ply.yacc as yacc
from jbp.error import error

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
from decimal import Decimal, InvalidOperation
from datetime import datetime

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
		'decimals': 2,
		'min': Decimal(-maxsize).quantize(Decimal('0.01')),
		'max': Decimal(+maxsize).quantize(Decimal('0.01')),
		'separator': '.'
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
	def __init__(self, strValue):
		self.strValue = strValue

#---------------------------------------------------------------

class declaration:
	def __init__(self, name, kind, specs):
		self.name = name
		self.kind = kind
		self.specs = specs
		self.arraySpecs = None
		self.optional = False

	@property
	def isArray(self):
		return (None != self.arraySpecs)

	def makeArray(self, arraySpecs):
		self.arraySpecs = arraySpecs

	def setOptional(self):
		self.optional = True

	def __str__(self):
		return f"{self.kind} -> {self.specs}"

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
	global adhoc_types
	global enums
	global nodes
	global root

	derived_types = dict()
	adhoc_types = dict()
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
	    root : ROOT '{' attributes '}'
			     | ROOT '{' '}'

	'''

	if len(p) < 5:
		msg = "Empty root node"
		raise ParseException(msg)

	global root
	if None != root:
		msg = 'Only one root can be defined'
		raise ParseException(msg)

	root = dict()

	attributes = p[3]
	for attr in attributes:
		root[attr.name] = attr

	p[0] = root


def p_node(p):
	'''
		node : NODE IDENTIFIER EXTENDS IDENTIFIER '{' attributes '}'
		     | NODE IDENTIFIER '{' attributes '}'
	'''

	if len(p) == 8:
		base_node = p[4]
		if not base_node in nodes:
			msg = f"Node '{base_node}' is not defined"
			raise ParseException(msg)

		base_decls = nodes[base_node]
		own_decls = p[6]
		own_name = p[2]

		for own_decl in own_decls:
			if own_decl.name in base_decls:
				msg = f"Field '{own_decl.name}' in node '{own_name}' is already defined in base node '{base_node}'"
				raise ParseException(msg)

		node_decls = dict()
		for decl in own_decls:
			node_decls[decl.name] = decl

		node_decls.update(base_decls)
		nodes[own_name] = node_decls

	else:
		own_name = p[2]
		own_decls = p[4]

		node_decls = dict()
		for decl in own_decls:
			node_decls[decl.name] = decl

		nodes[own_name] = node_decls


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
			type : TYPE element_declaration
	'''

	decl = p[2]
	new_kind = create_type(decl)
	derived_types[decl.name] = new_kind
	p[0] = decl


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
		p[2].setOptional()
		p[0] = p[2]

	else:
		p[0] = p[1]


def p_attribution(p):
	'''
		attribution : array_declaration
		            | local_declaration
	'''

	p[0] = p[1]


def p_array_declaration(p):
	'''
		array_declaration : local_declaration '[' specificities ']'
		                  | local_declaration '[' ']'
	'''

	specs = {
		'min': 1,
		'max': maxsize,
	}
	
	if len(p) == 5:
		for specificity in p[3]:
			field, value = specificity

			if not field in specs:
				msg = f"Invalid specificity for array: '{field}'"
				raise ParseException(msg)

			specs[field] = value

	p[1].makeArray(specs)
	p[0] = p[1]


def p_local_declaration(p):
	'''
		local_declaration : element_declaration
	'''
	
	decl = p[1]
	if len(decl.specs) > 0:
		new_kind = create_type(decl)
		adhoc_type = '_anonymous_' + str(len(adhoc_types)) + '_'
		adhoc_types[adhoc_type] = new_kind
		decl.kind = adhoc_type

	p[0] = decl


def p_element_declaration(p):
	'''
		element_declaration : IDENTIFIER ':' IDENTIFIER '(' specificities ')'
		                    | IDENTIFIER ':' IDENTIFIER
	'''

	kind = p[3]
	kind_exists = (
		kind in primitive_types or
		kind in derived_types or
		kind in enums or
		kind in nodes)
	
	if not kind_exists:
		msg = f"Unknown type '{kind}'"
		raise ParseException(msg)

	ident = p[1]
	specs = p[5] if len(p) == 7 else list()
	p[0] = declaration(ident, kind, specs)


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

	try:
		rawValue = int(strValue)
		if not specs['min'] <= rawValue <= specs['max']:
			return False, error(error.OUTSIDE_RANGE,
				field=fieldName, value=rawValue)

	except ValueError as e:
		return False, error(error.INTEGER_PARSING,
			text=strValue)

	return True, rawValue


def d_float(fieldName, value, specs):
	strValue = value.strValue if isinstance(value, taggedNumber) else value

	try:
		sanedValue = strValue.replace('Infinity', 'inf')
		rawValue = float(sanedValue)

		if not specs['min'] <= rawValue <= specs['max']:
			return False, error(error.OUTSIDE_RANGE,
				field=fieldName, value=rawValue)

	except ValueError as e:
		return False, error(error.FLOAT_PARSING,
			text=strValue)

	return True, rawValue


def d_fixed(fieldName, value, specs):
	strValue = value.strValue if isinstance(value, taggedNumber) else value
	sanedStrValue = strValue.replace(specs['separator'], '.')

	try:
		precision = f"1e-{specs['decimals']}"
		rawValue = Decimal(sanedStrValue).quantize(Decimal(precision))
		if specs['min'] > rawValue or rawValue > specs['max']:
			return False, error(error.OUTSIDE_RANGE,
				field=fieldName, value=rawValue)

	except InvalidOperation as e:
		return False, error(error.FIXED_PARSING,
			text=strValue)

	return True, rawValue


def d_bool(fieldName, value, specs):
	value = value.strValue if isinstance(value, taggedNumber) else value

	if isinstance(value, bool):
		return True, value

	if not specs['coerce']:
		return False, error(error.INVALID_BOOLEAN, value=value)

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

	except ValueError as e:
		return False, f"'{strValue}' doesn't match expected datetime format"


def d_string(fieldName, strValue, specs):
	if not isinstance(strValue, str):
		return False, error(error.INVALID_STRING,
			field=fieldName, value=strValue)

	strLength = len(strValue)
	if not specs['minLength'] <= strLength <= specs['maxLength']:
		return False, error(error.INVALID_LENGTH,
			field=fieldName, length=strLength)

	return True, strValue

#---------------------------------------------------------------

import json

class blueprint:
	def __init__(self, contents):
		lexer = lex.lex()
		parser = yacc.yacc()
		parser.parse(contents)

		self.root = root
		self.derived_types = derived_types
		self.adhoc_types = adhoc_types
		self.nodes = nodes
		self.enums = enums

	def __str__(self):
		return (f'types = {self.derived_types} '
			+ f'adhoc = {self.adhoc_types} '
			+ f'enums = {self.enums} '
			+ f'nodes = {self.nodes} '
			+ f'root = {self.root}')


	def deserialize_field(self, decl, retrieved):
		if decl.kind in primitive_types:
			specs = primitive_types[decl.kind]
			baseType = decl.kind

		elif decl.kind in derived_types:
			specs = self.derived_types[decl.kind]
			baseType = specs['__baseType__']

		else:
			specs = self.adhoc_types[decl.kind]
			baseType = specs['__baseType__']

		deserialize_method = globals()['d_' + baseType]
		return deserialize_method(decl.name, retrieved, specs)


	def validate_enum(self, value, enumType):
		possibleValues = self.enums[enumType]
		if not value in possibleValues:
			return False, f'Unknown {enumType} value: "{value}"'
		
		return True, value


	def validate_array(self, decl, contents):
		if not isinstance(contents, list):
			return False, f'Field "{decl.name}" needs to be an array'

		arrayMin = decl.arraySpecs['min']
		arrayMax = decl.arraySpecs['max']
		arrayLen = len(contents)
		
		if arrayLen < arrayMin:
			return False, f"Array '{decl.name}' needs to have at least {arrayMin} elements, found {arrayLen}"
		
		if arrayLen > arrayMax:
			return False, f"Array '{decl.name}' needs to have at most {arrayMax} elements, found {arrayLen}"

		if decl.kind in self.nodes:
			arrayNode = self.nodes[decl.kind]

			for content in contents:
				success, result = self.validate_node(arrayNode, content)
				if not success: return False, result

			return True, decl

		if decl.kind in self.enums:
			for value in contents:
				success, processed = self.validate_enum(value, decl.kind)
				if not success: return False, processed

			return True, decl

		for idx, value in enumerate(contents):
			success, processed = self.deserialize_field(decl, value)
			if not success: return False, f"Array '{decl.name}' at index {idx}: {processed}"
			contents[idx] = processed

		return True, contents


	def validate_node(self, node, contents):
		if not isinstance(contents, dict):
			return False, f'Invalid data'

		for attr, decl in node.items():
			if not attr in contents:
				if decl.optional: continue
				return False, f'Missing field "{attr}"'

			retrieved = contents[attr]
			attr_type = decl.kind

			if decl.isArray:
				success, processed = self.validate_array(decl, retrieved)
				if not success: return success, processed
				continue

			if attr_type in self.nodes:
				node_decl = self.nodes[attr_type]
				success, processed = self.validate_node(node_decl, retrieved)
				if not success: return success, processed
				continue

			if attr_type in self.enums:
				success, processed = self.validate_enum(retrieved, attr_type)
				if not success: return success, processed
				continue

			success, processed = self.deserialize_field(decl, retrieved)
			if not success: return False, processed
			contents[attr] = processed

		return True, contents


	def validate(self, root_contents):
		return self.validate_node(self.root, root_contents)


	def deserialize(self, contents):
		tag_number = lambda x : taggedNumber(x)
		ident = lambda x : x

		try:
			loaded = json.loads(contents,
				parse_float=tag_number, parse_int=tag_number,
				parse_constant=ident)

		except json.JSONDecodeError as e:
			return False, f'Invalid JSON, error at line {e.lineno}, column {e.colno}: {e.msg}'
	
		return self.validate(loaded)

#-------------------------------------------------------------------------------

from threading import Lock
mutex = Lock()

def load(filename):
	with open(filename, "r") as fd:
		contents = fd.read()
		return loads(contents)


def loads(contents):
	with mutex:
		initGlobals()
		result = blueprint(contents)
		return result

