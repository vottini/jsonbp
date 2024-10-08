
from decimal import Decimal
from .ply import lex as plyLex
from .ply import yacc as plyYacc

from .types import FieldType
from .exception import SchemaViolation
from .error import print_warning, print_error
from .loader import load_types
from .blueprint import JsonBlueprint
from .declaration import create_declaration
from .field import create_field
from .array import make_array

reserved = (
	'root',
	'object',
	'type',
	'enum',
	'optional',
	'nullable',
	'extends',
	'include'
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
	'FLOAT_CONST',
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
	t.value = Decimal(t.value)
	return t

def t_FLOAT_CONST(t):
	r'[+-]?Infinity|NaN'
	sanedValue = t.value.replace('Infinity', 'inf')
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

def t_error(t):
	sentence = t.value.split()[0]
	msg = f"Syntax error: Unexpected sentence '{sentence}' on line {t.lineno}"
	raise SchemaViolation(msg)

def p_error(p):
	if p == None: raise SchemaViolation("Empty blueprint")
	msg = f"Error parsing line {p.lineno}: token '{p.value}' misplaced"
	raise SchemaViolation(msg)

#---------------------------------------------------------------

def typeExists(typeName, excluded=None):
	excluded = excluded or set()

	lookups = (
	  currentBlueprint._find_object_decl,
	  currentBlueprint._find_element_decl,
	  currentBlueprint._find_enum_decl
	)

	for method in lookups:
	  found = method(typeName, excluded.copy())
	  if found is not None:
	    return True

	return False


adhoc_counter = 0
def getNextAdhoc():
	global adhoc_counter
	adhoc_counter += 1
	return adhoc_counter

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
	                 | object
	                 | root
	                 | include
	'''

#---------------- constructs -----------------------------


def p_include(p):
	'''
	  include : INCLUDE STRING
	'''

	inclusionFile = p[2]
	inclusionPath = os.path.join(currentPath, inclusionFile)
	pushEnv()

	try: loadedBlueprint = load_file(inclusionPath)
	except SchemaViolation as e: raise SchemaViolation(e)
	finally: popEnv()

	for typeName in loadedBlueprint._collect_types():
	  if typeExists(typeName, excluded=loadedBlueprint._collect_sources()):
	    raise SchemaViolation(
	      f"Error including '{inclusionFile}': "
	      f"type '{typeName}' already defined"
	    )

	currentBlueprint.includes.append(loadedBlueprint)


def p_root(p):
	'''
	    root : ROOT array_declaration
	         | ROOT single_declaration

	'''

	if None != currentBlueprint.root:
	  msg = 'Only one root can be defined'
	  raise SchemaViolation(msg)

	currentBlueprint.root = p[2]


def p_object(p):
	'''
	  object : OBJECT IDENTIFIER EXTENDS IDENTIFIER object_declaration
	         | OBJECT IDENTIFIER object_declaration
	'''

	objectName = p[2]
	if typeExists(objectName):
	  msg = f"Duplicated type '{objectName}'"
	  raise SchemaViolation(msg)

	if len(p) == 6:
	  baseObject = p[4]
	  baseFields = currentBlueprint._find_object_decl(baseObject)

	  if None == baseFields:
	    msg = f"Object '{baseObject}' is not defined"
	    raise SchemaViolation(msg)

	  objectFields = p[5]
	  for fieldName, fieldDeclaration in objectFields.items():
	    if fieldName in baseFields:
	      raise SchemaViolation(
	        f"Field '{fieldName}' in object '{objectName}' "
	        f"is already defined in base object '{baseObject}'"
	      )

	  objectFields.update(baseFields)
	  currentBlueprint.objects[objectName] = objectFields

	else:
	  objectFields = p[3]
	  currentBlueprint.objects[objectName] = objectFields


def p_object_specs(p):
	'''
	  object_declaration : '{' attributes '}'
	'''

	decls = p[2]
	newObject = dict()
	for decl in decls:
	  newObject[decl[0]] = decl[1]

	p[0] = newObject


def createType(newTypeName, declaration):
	base_type = declaration.typeName
	origin = currentBlueprint._find_element_decl(
	  base_type)

	newType = dict()
	for specName, value in origin.items():
	  newType[specName] = value

	for spec in declaration.specs:
	  specName, value = spec
	  if not specName in origin:
	    raise SchemaViolation(
	      f"Type '{newTypeName}' ({declaration.typeName}) "
	      f"has no attribute '{specName}'"
	    )

	  oldValue = newType[specName]
	  if type(oldValue) == float and type(value) == Decimal: value = float(value)
	  if type(oldValue) == float and type(value) == int: value = float(value)

	  if type(value) != type(oldValue):
	    raise SchemaViolation(
	      f"New value for specificity '{specName}' is {type(value).__name__}, "
	      f"but it expects {type(oldValue).__name__}"
	    )

	  newType[specName] = value

	while not base_type in currentBlueprint.primitive_types:
	  parent_type = currentBlueprint.derived_types[base_type]
	  base_type = parent_type['__baseType__']

	newType['__baseType__'] = base_type
	currentBlueprint.derived_types[newTypeName] = newType
	return newType


def p_type(p):
	'''
	    type : TYPE IDENTIFIER ':' element_declaration
	'''

	typeName = p[2]
	if typeExists(typeName):
	  msg = f"Duplicated type '{typeName}'"
	  raise SchemaViolation(msg)

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
	  fieldData.optional = True
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

	jArray = make_array(p[1])

	if len(p) == 5:
	  for specificity in p[3]:
	    spec, value = specificity
	    jArray.apply_spec(spec, value)

	p[0] = jArray


def p_single_declaration(p):
	'''
	  single_declaration : NULLABLE atomic_declaration
	                     | atomic_declaration
	'''

	if len(p) == 3:
	  p[2].nullable = True
	  p[0] = p[2]
	  return

	p[0] = p[1]


def p_atomic_declaration(p):
	'''
	  atomic_declaration : object_declaration
	                     | enum_declaration
	                     | element_declaration
	'''

	declaration = p[1]
	if isinstance(declaration, dict):
	  adhoc_object = '_object_type_' + str(getNextAdhoc()) + '_'
	  currentBlueprint.objects[adhoc_object] = declaration
	  kind = FieldType.OBJECT
	  fieldId = adhoc_object

	elif isinstance(declaration, list):
	  adhoc_enum = '_enum_type_' + str(getNextAdhoc()) + '_'
	  currentBlueprint.enums[adhoc_enum] = declaration
	  kind = FieldType.ENUM
	  fieldId = adhoc_enum

	else:
	  declType = declaration.typeName
	  if currentBlueprint._find_element_decl(declType) is not None:
	    kind = FieldType.SIMPLE

	    if not declaration.isCustomized():
	      fieldId = declaration.typeName

	    else:
	      adhoc_type = '_simple_type_' + str(getNextAdhoc()) + '_'
	      createType(adhoc_type, declaration)
	      fieldId = adhoc_type

	  elif currentBlueprint._find_enum_decl(declType):
	    kind = FieldType.ENUM
	    fieldId = declType

	  else:
	    kind = FieldType.OBJECT
	    fieldId = declType

	p[0] = create_field(kind, fieldId)


def p_element_declaration(p):
	'''
	  element_declaration : IDENTIFIER '(' specificities ')'
	                      | IDENTIFIER
	'''

	typeName = p[1]

	if len(p) == 5:
	  not_simple = (
	    currentBlueprint._find_object_decl(typeName) or
	    currentBlueprint._find_enum_decl(typeName))

	  if not_simple:
	    raise SchemaViolation(
	      f"Unable to apply specificities to '{typeName}', "
	      "only simple types can be specialized")

	  if not currentBlueprint._find_element_decl(typeName):
	    msg = f"Unknown simple type '{typeName}'"
	    raise SchemaViolation(msg)

	  specs = p[3]

	else:
	  if not typeExists(typeName):
	    msg = f"Type not declared: '{typeName}'"
	    raise SchemaViolation(msg)

	  specs = list()

	p[0] = create_declaration(typeName, specs)


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
	                    | FLOAT_CONST
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
	if typeExists(enum_name):
	  msg = f"Duplicated type '{enum_name}'"
	  raise SchemaViolation(msg)

	currentBlueprint.enums[enum_name] = p[3]


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

_mutex = Lock()
_loadedFiles = dict()
_pushedEnvs = list()

def setupEnv(contentPath, output):
	global currentBlueprint, currentPath
	currentPath = contentPath
	currentBlueprint = output


def pushEnv():
	env = (currentPath, currentBlueprint)
	_pushedEnvs.append(env)
	_mutex.release()


def popEnv():
	global currentPath, currentBlueprint

	_mutex.acquire()
	env = _pushedEnvs.pop()
	(currentPath, currentBlueprint) = env

#---------------------------------------------------------------

def _load(contents, contentPath, contentName, typeDirs):
	lexer = plyLex.lex()
	parser = plyYacc.yacc()

	ownPath = os.path.dirname(os.path.realpath(__file__))
	primitivesPath = os.path.join(ownPath, "types")
	loaded, notLoaded = load_types(primitivesPath)

	primitive_types = dict()
	for typeSpec in loaded:
	  name = typeSpec['name']
	  primitive_types[name] = typeSpec

	if typeDirs is not None:
	  for typeDir in typeDirs:
	    loaded, notLoaded = load_types(typeDir)

	    if len(loaded) == len(notLoaded) == 0:
	      msg = f"No files found in dir '{typeDir}'"
	      print_warning(msg)
	      continue

	    for typeSpec in loaded:
	      name = typeSpec['name']
	      if name in primitive_types:
	        msg = f"Overwriting previously defined type '{name}'"
	        print_warning(msg)

	      primitive_types[name] = typeSpec

	    for file, problem in notLoaded:
	      msg = f"Unable to load file '{file}' => {problem}"
	      print_error(msg)

	try:
	  _mutex.acquire()
	  result = JsonBlueprint(primitive_types)
	  setupEnv(contentPath, result)
	  parser.parse(contents)

	  if None != contentName:
	    contentFullpath = os.path.join(contentPath, contentName)
	    abspath = os.path.abspath(contentFullpath)
	    _loadedFiles[abspath] = result

	  return result

	finally:
	  _mutex.release()

#------------------------------------------------------------------------------

import os

def load_file(filepath, **kwargs):

	'''Loads a :class:`JsonBlueprint` from a file.

	On success, the  returned instance is associated with the
	absolute path of the argument file, and subsequent calls of this
	function to the same file will be presented with the same instance,
	unless :func:`invalidate_cache` is invoked.

	Args:
	  filepath (str): schema file to load.
	  **custom_types (str[]): list of directories to scan for primitive types.

	Returns:
	  JsonBlueprint: the generated blueprint

	Raises:
	  SchemaViolation: when the schema is malformed or there are inconsistencies
	    in its relations

	'''

	abspath = os.path.abspath(filepath)
	if abspath in _loadedFiles:
	  return _loadedFiles[abspath]

	try:
	  with open(filepath, "r") as fd:
	    contents = fd.read()

	except FileNotFoundError:
	  msg = f'Unable to open file "{filepath}"'
	  raise SchemaViolation(msg)

	return _load(contents,
	  os.path.dirname(filepath),
	  os.path.basename(filepath),
	  kwargs.get('custom_types'))


def load_string(schema, **kwargs):

	'''Loads a :class:`JsonBlueprint` from the contents of a string.

	Args:
	  schema (str): schema definition.
	  **custom_types (str[]): list of directories to scan for primitive types.

	Returns:
	  JsonBlueprint: the generated blueprint

	Raises:
	  SchemaViolation: when the schema is malformed or there are inconsistencies
	    in its relations

	'''

	return _load(schema, '.', None,
	  kwargs.get('custom_types'))

#-------------------------------------------------------------------------------

def invalidate_cache():
	'''Clears associations between files and existing JsonBlueprint instances.

	This forces new :func:`load_file` invocations to effectively parse the files instead
	of returning a cached result (Useful when your schema file changed and needs
	to be refreshed).

	'''

	global _loadedFiles

	try:
	  _mutex.acquire()
	  _loadedFiles = dict()

	finally:
	  _mutex.release()

