
import ply.lex as lex
import ply.yacc as yacc

import jbp.declaration as jbpDeclaration
import jbp.field as jbpField
import jbp.array as jbpArray
import jbp.blueprint as jbpBlueprint

from jbp.types import primitive_types
from decimal import Decimal

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

class TokenException(Exception): pass
class ParseException(Exception): pass

def t_error(t):
	msg = f"Illegal character '{t.value[0]}' on line {t.lineno}"
	raise TokenException(msg)

def p_error(p):
	if p == None: raise ParseException("Empty blueprint")
	msg = f"Syntax error in line {p.lineno}: token '{p.value}' misplaced"
	raise ParseException(msg)

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
	    root : ROOT array_declaration
					 | ROOT single_declaration

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

	nodeName = p[2]
	name_is_taken = (
		nodeName in nodes or
		nodeName in enums or
		nodeName in primitive_types or
		nodeName in derived_types)

	if name_is_taken:
			msg = f"Duplicated type '{nodeName}'"
			raise ParseException(msg)

	if len(p) == 6:
		baseNode = p[4]
		if not baseNode in nodes:
			msg = f"Node '{baseNode}' is not defined"
			raise ParseException(msg)

		baseFields = nodes[baseNode]
		nodeFields = p[5]

		for fieldName, fieldDeclaration in nodeFields.items():
			if fieldName in baseFields:
				msg = f"Field '{fieldName}' in node '{nodeName}' is already defined in base node '{baseNode}'"
				raise ParseException(msg)

		nodeFields.update(baseFields)
		nodes[nodeName] = nodeFields

	else:
		nodeFields = p[3]
		nodes[nodeName] = nodeFields


def p_node_specs(p):
	'''
		node_declaration : '{' attributes '}'
	'''

	decls = p[2]
	newNode = dict()
	for decl in decls:
		newNode[decl[0]] = decl[1]

	p[0] = newNode


def createType(newTypeName, declaration):
	origin = (
		primitive_types[declaration.typeName]
			if declaration.typeName in primitive_types
			else derived_types[declaration.typeName])

	newType = dict()
	for specName, value in origin.items():
		newType[specName] = value

	for spec in declaration.specs:
		specName, value = spec
		if not specName in origin:
			msg = f"Type '{newTypename}' ({declaration.typeName}) has no attribute {specName}"
			raise ParseException(msg)

		oldValue = newType[specName]
		if type(oldValue) == Decimal and type(value) == float: value = Decimal(value)
		if type(oldValue) == float and type(value) == int: value = float(value)

		if type(value) != type(oldValue):
			msg = f"New value for specificity '{specName}' is {type(value).__name__}, but it expects {type(oldValue).__name__}"
			raise ParseException(msg)

		newType[specName] = value

	base_type = declaration.typeName
	while not base_type in primitive_types:
		parent_type = derived_types[base_type]
		base_type = parent_type['__baseType__']

	newType['__baseType__'] = base_type
	derived_types[newTypeName] = newType
	return newType


def p_type(p):
	'''
			type : TYPE IDENTIFIER ':' element_declaration
	'''

	typeName = p[2]
	declaration = p[4]
	createType(typeName, declaration)


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
		fieldName, fieldData = p[2]
		fieldData.setOptional()
		p[0] = p[2]

	else:
		p[0] = p[1]


def p_attribution(p):
	'''
		attribution : IDENTIFIER ':' array_declaration
		            | IDENTIFIER ':' single_declaration
	'''

	p[0] = (p[1], p[3])


def p_array_declaration(p):
	'''
		array_declaration : single_declaration '[' specificities ']'
		                  | single_declaration '[' ']'
	'''

	jArray = jbpArray.makeArray(p[1])
	
	if len(p) == 5:
		for specificity in p[3]:
			spec, value = specificity
			jArray.applySpec(spec, value)

	p[0] = jArray


def p_single_declaration(p):
	'''
		single_declaration : node_declaration
		                   | enum_declaration
		                   | element_declaration
	'''
	
	declaration = p[1]
	if isinstance(declaration, dict):
		adhoc_node = '_node_type_' + str(len(nodes)) + '_'
		nodes[adhoc_node] = declaration
		fieldKind = jbpField.NODE
		fieldType = adhoc_node

	elif isinstance(declaration, list):
		adhoc_enum = '_enum_type_' + str(len(enums)) + '_'
		enums[adhoc_enum] = declaration
		fieldKind = jbpField.ENUM
		fieldType = adhoc_enum

	else:
		declType = declaration.typeName
		if declType in primitive_types or declType in derived_types:
			fieldKind = jbpField.SIMPLE

			if not declaration.isCustomized():
				fieldType = declaration.typeName

			else:
				adhoc_type = '_simple_type_' + str(len(derived_types)) + '_'
				createType(adhoc_type, declaration)
				fieldType = adhoc_type

		elif declType in enums:
			fieldKind = jbpField.ENUM
			fieldType = declType

		elif declType in nodes:
			fieldKind = jbpField.NODE
			fieldType = declType

	p[0] = jbpField.create(fieldKind, fieldType)


def p_element_declaration(p):
	'''
		element_declaration : IDENTIFIER '(' specificities ')'
		                    | IDENTIFIER
	'''

	typeName = p[1]

	if len(p) == 5:
		isComplex = (
			typeName in enums or
			typeName in nodes)

		if isComplex:
			msg = f"Unable to apply specificities to '{typeName}', only simple types can be specialized"
			raise ParseException(msg)

		typeExists = (
			typeName in primitive_types or
			typeName in derived_types)
	
		if not typeExists:
			msg = f"Unknown simple type '{typeName}'"
			raise ParseException(msg)

		specs = p[3]

	else:
		typeExists = (
			typeName in primitive_types or
			typeName in derived_types or
			typeName in enums or
			typeName in nodes)

		if not typeExists:
			msg = f"Unknown simple type '{typeName}'"
			raise ParseException(msg)

		specs = list()
	
	p[0] = jbpDeclaration.create(typeName, specs)


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
			enum : ENUM IDENTIFIER enum_declaration
	'''

	enum_name = p[2]
	name_is_taken = (
		enum_name in nodes or
		enum_name in enums or
		enum_name in primitive_types or
		enum_name in derived_types)

	if name_is_taken:
			msg = f"Duplicated type '{enum_name}'"
			raise ParseException(msg)

	enums[enum_name] = p[3]


def p_enum_declaration(p):
	'''
			enum_declaration : '{' constants '}'
	'''

	p[0] = p[2]


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

from threading import Lock
mutex = Lock()

def initGlobals():
	global derived_types
	global enums
	global nodes
	global root

	derived_types = dict()
	enums = dict()
	nodes = dict()
	root = None

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
		result = jbpBlueprint.JsonBlueprint(root, derived_types, nodes, enums)
		return result

