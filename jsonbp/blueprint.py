
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

identity = lambda x : x
unquote = lambda x : unquoted_str(x)

#-------------------------------------------------------------------------------

class JsonBlueprint:
  """
    Class to serialize Python objects to JSON strings and vice-versa.
  """

  def __init__(self, primitive_types):
    self.uuid = uuid.uuid4()
    self.includes = list()
    self.primitive_types = primitive_types
    self.derived_types = dict()
    self.enums = dict()
    self.objects = dict()
    self.root = None

  def __str__(self): # pragma: no cover
    return (
      f"blueprint: {self.uuid}\n" +
      f"|-> primitive types = {self.primitive_types}\n" +
      f"|-> derived types = {self.derived_types}\n" +
      f"|-> enums = {self.enums}\n" +
      f"|-> objects = {self.objects}\n" +
      f"'-> root = {self.root}")

  #-----------------------------------------------------------------------------

  def _validate_field(self, field_name, field_type, value):
    if field_type in self.primitive_types:
      specs = self.primitive_types[field_type]['defaults']
      baseType = field_type

    else:
      specs = self._find_element_decl(field_type)
      baseType = specs['__baseType__']

    try:
      deserializeMethod = self.primitive_types[baseType]['parser']
      success, outcome = deserializeMethod(value, specs)

      if not success:
        return False, create_field_error(field_name,
          outcome["error"], type=baseType,
          **outcome["context"])

      return success, outcome

    except Exception as e:
      return False, create_field_error(field_name,
        ErrorType.VALUE_PARSING, type=baseType)


  def _validate_enum(self, field_name, enum_type, value):
    if isinstance(value, unquoted_str):
      return False, create_field_error(field_name,
        ErrorType.INVALID_ENUM, value=value)

    possibleValues = self._find_enum_decl(enum_type)

    if not value in possibleValues:
      return False, create_field_error(field_name,
        ErrorType.UNKNOWN_LITERAL, value=value)

    return True, value


  def _validate_array(self, field_name, jArray, contents):
    if not isinstance(contents, collections.abc.Sequence):
      return False, create_field_error(field_name,
        ErrorType.INVALID_ARRAY)

    array_len = len(contents)
    if not jArray.minLength <= array_len <= jArray.maxLength:
      return False, create_field_error(field_name,
        ErrorType.INVALID_LENGTH, length=array_len)

    array_kind = jArray.fieldKind
    array_type = jArray.fieldType

    element_type = array_type
    deserializer = (self._validate_enum if array_kind == FieldType.ENUM
      else self._validate_field)

    if array_kind == FieldType.OBJECT:
      element_type = self._find_object_decl(array_type)
      deserializer = self._validate_object

    result = list()
    for idx, value in enumerate(contents):
      if value is None:
        if jArray.nullable:
          result.append(None)
          continue

        return False, create_object_error(field_name,
          ErrorType.NULL_VALUE, field=field_name)

      success, outcome = deserializer(
        field_name,
        element_type,
        value)

      if not success:
        field_error = outcome
        field_error.set_as_array_index(idx)
        return False, field_error

      processed = outcome
      result.append(processed)

    return True, result


  def _validate_object(self, object_name, objectInstance, contents):
    if not isinstance(contents, collections.abc.Mapping):
      return False, create_object_error(object_name,
        ErrorType.INVALID_OBJECT)

    result = dict()
    for field_name, field_data in objectInstance.items():
      if not field_name in contents:
        if field_data.optional:
          continue

        return False, create_object_error(object_name,
          ErrorType.MISSING_FIELD, field=field_name)

      retrieved = contents[field_name]

      if is_array(field_data):
        if retrieved is None:
          if field_data.nullableArray:
            result[field_name] = None
            continue

          else:
            return False, create_object_error(object_name,
              ErrorType.NULL_VALUE, field=field_name)

        success, outcome = self._validate_array(
          field_name, field_data,
          retrieved)

        if not success:
          field_error = outcome
          return False, field_error

        processed = outcome
        result[field_name] = processed
        continue

      if retrieved is None:
        if field_data.nullable:
          result[field_name] = None
          continue

        return False, create_object_error(object_name,
          ErrorType.NULL_VALUE, field=field_name)

      field_kind = field_data.fieldKind
      field_type = field_data.fieldType

      if field_kind == FieldType.OBJECT:
        objectSpecs = self._find_object_decl(field_type)
        success, outcome = self._validate_object(
          field_name, objectSpecs,
          retrieved)

        if not success:
          field_error = outcome
          return False, field_error

        processed = outcome
        result[field_name] = processed
        continue

      if field_kind == FieldType.ENUM:
        success, outcome = self._validate_enum(
          field_name, field_type,
          retrieved)

        if not success:
          field_error = outcome
          return False, field_error

        processed = outcome
        result[field_name] = processed
        continue

      success, outcome = self._validate_field(
        field_name, field_type,
        retrieved)

      if not success:
        field_error = outcome
        return False, field_error

      processed = outcome
      result[field_name] = processed

    return True, result


  def validate(self, root_contents):
    if is_array(self.root):
      if root_contents is not None:
        return self._validate_array(None, self.root,
          root_contents)

        if self.root.nullableArray:
          return True, None

        else:
          return False, create_object_error(None,
            ErrorType.NULL_VALUE, field="root")

    if None == root_contents:
      if self.root.nullable:
        return True, None

      else:
        return False, create_object_error(None,
          ErrorType.NULL_VALUE, field="root")

    root_kind = self.root.fieldKind
    root_type = self.root.fieldType

    if root_kind == FieldType.OBJECT:
      root_object = self._find_object_decl(root_type)
      return self._validate_object(None, root_object,
        root_contents)

    if root_kind == FieldType.ENUM:
      return self._validate_enum(None, root_type,
        root_contents)

    if root_kind == FieldType.SIMPLE:
      return self._validate_field(None, root_type,
        root_contents)


  def deserialize(self, contents):
    """Attempts to deserialize a JSON string into a Python object.

    The returned tuple's first element indicates whether the deserialization
    was successful. When deserialization succeeds the respective Python data
    will be the second element. Conversely, when a problem is found the first
    element will be False and the second element will be an instance of
    :class:`DeserializationError`.

    Args:
      contents (str): JSON string to deserialize into Python data.

    Returns:
      Tuple[bool, object]

    """

    if self.root is None:
      msg = "No root defined for blueprint, unable to deserialize"
      raise SchemaViolation(msg)

    try:
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
      collected.extend(source.derived_types.keys())
      collected.extend(source.enums.keys())
      collected.extend(source.objects.keys())

    return collected


  def __hash__(self):
    return hash(self.uuid)

  #----------------------------------------------------------------------------

  def _find_element_decl(self, typeName, checked=None):
    if typeName in self.primitive_types: return self.primitive_types[typeName]['defaults']
    if typeName in self.derived_types: return self.derived_types[typeName]
    checked = checked or set()
    checked.add(self)

    for blueprint in self.includes:
      if not blueprint in checked:
        found = blueprint._find_element_decl(typeName, checked)
        if None != found: return found

    return None


  def _find_object_decl(self, object_name, checked=None):
    if object_name in self.objects: return self.objects[object_name]
    checked = checked or set()
    checked.add(self)

    for blueprint in self.includes:
      if not blueprint in checked:
        found = blueprint._find_object_decl(object_name, checked)
        if None != found: return found

    return None


  def _find_enum_decl(self, enum_name, checked=None):
    if enum_name in self.enums:
      return self.enums[enum_name]

    checked = checked or set()
    checked.add(self)

    for blueprint in self.includes:
      if not blueprint in checked:
        found = blueprint._find_enum_decl(enum_name, checked)
        if None != found:
          return found

    return None

  #----------------------------------------------------------------------------

  def choose_root(self, root_type, as_array=False,
    min_array_length=None, max_array_length=None):

    """Selects or changes the root element of a blueprint.

      This function allows you to select or overwrite the root
      type of a blueprint file when no root is defined, or when you want
      to use a different root for serializing/deserializing data with a
      JsonBlueprint instance. The original JsonBlueprint instance remains
      unchanged; instead, a new instance is created with the same context,
      but with the modified root type.

      Args:
        root_type (str): name of the type to be used as root.
		    as_array (bool): whether the chosen root is an array or not of the selected type.
        min_array_length (int): if set as array, minimum size that the root must be.
        max_array_length (int): if set as array, maximum size that the root can be.

      Returns:
        A new blueprint, with the root selected or replaced.

      Raises:
        SchemaViolation: when the given type doesn't exist
	        within the blueprint context.

    """

    lookups = [
      (self._find_object_decl, FieldType.OBJECT),
      (self._find_element_decl, FieldType.SIMPLE),
      (self._find_enum_decl, FieldType.ENUM)
    ]

    found_root = None
    root_kind = None

    for method, kind in lookups:
      if candidate := method(root_type, set()):
        found_root = candidate
        root_kind = kind
        break

    if found_root is None:
      msg = f"No element found with name '{root_type}'"
      raise SchemaViolation(msg)

    root_field = create_field(root_kind, root_type)
    result = JsonBlueprint(self.primitive_types)
    result.root = (make_array(root_field) if as_array else
      root_field)

    if as_array:
      if min_array_length: result.root.apply_spec('minLength', min_array_length)
      if max_array_length: result.root.apply_spec('maxLength', max_array_length)

    result.includes = self.includes
    result.derived_types = self.derived_types
    result.enums = self.enums
    result.objects = self.objects

    return result

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


  def _serialize_object(self, object_type, object_name, content):
    objectInstance = self._find_object_decl(object_type)

    if not isinstance(content, collections.abc.Mapping):
      msg = f"{object_name} needs to receive a dict to serialize"
      raise SerializationException(msg)

    serialized = list()
    for field_name, field_data in objectInstance.items():
      if not field_name in content:
        if field_data.optional:
          continue

        msg = f"{object_name}: missing field {field_name}"
        raise SerializationException(msg)

      fieldValue = content[field_name]
      processed = self._serialize_element(field_data, field_name, fieldValue)
      serialized.append(f'"{field_name}":{processed}')

    inner = ",".join(serialized)
    return f"{{{inner}}}"


  def _serialize_enum(self, enum_type, field_name, content):
    possibleValues = self._find_enum_decl(enum_type)

    if not content in possibleValues:
      msg = f"Value '{content}' is not valid for field '{field_name}'"
      raise SerializationException(msg)

    return f'"{content}"'


  def _serialize_field(self, field_type, field_name, content):
    if field_type in self.primitive_types:
      specs = self.primitive_types[field_type]['defaults']
      baseType = field_type

    else:
      specs = self._find_element_decl(field_type)
      baseType = specs['__baseType__']

    serialize_method = self.primitive_types[baseType]['formatter']
    return serialize_method(content, specs)

  #-------------------------------------------------------------------------------

  def serialize(self, content):
    """Attempts to serialize a Python object into a JSON string.

      Args:
        content (object): Python data to be transformed into
          a JSON string.

      Returns:
        the resulting JSON string

      Raises:
        SerializationException: when a field is missing in the
          Python object or some field has an incompatible type.

    """

    if self.root is None:
      msg = "No root defined for blueprint, unable to serialize"
      raise SerializationException(msg)

    if content is None:
      if self.root.nullable:
        return 'null'

    return self._serialize_element(
      self.root,
      "Root Level",
      content)

