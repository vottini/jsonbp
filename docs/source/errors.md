
# Error Handling

Errors related to jsonbp can happen at three stages:

- [During JSON deserialization](#json-deserialization)
- [During Python serialization](#python-serialization)
- [During Schema Parsing](#schema-parsing)

## JSON deserialization

These errors occur when your program receives a JSON input that is
either incomplete or that has an unexpected/undesired value. The blueprint
method **deserialize()** returns a pair of values, the first one indicates
whether the operation was successful or not. If the operation failed,
the second value holds an object that can be used to generate a message explaining
why the given input was not accepted.

Here's a full example ilustrating error reporting: we define a blueprint to accept
fields **'a'** and **'b'**, both of which must be stricly decimal. We then do some processing
on them and return the result with status 200 (success). If, however, the JSON input
is invalid, we return status 400 (bad request) along with the reason for the failure:

```py
import jsonbp

#------------------------------------

blueprint = '''
root {
  a: decimal,
  b: decimal
}
'''

blueprint = jsonbp.load_string(blueprint)

#------------------------------------

def add(data): return data['a'] + data['b']

#------------------------------------

def answer(statusCode, payload):
  print(f" => status: {statusCode} | payload: {payload}")

payloads = [
  '{"a": 42, "b": 1337}',
  '{"a": 1.2e3, "b": 1337}',
  '{"a": 42, "b": "Hello"}',
  '{"a": 42, "c": "30"}',
  '{"a": 42 "b": "30"}'
]

for received in payloads:
  print(received, end='')
  success, outcome = blueprint.deserialize(received)
  
  if success:
    data = outcome
    processed = add(data)
    response = {'sum': processed}
    answer(200, response)
  
  else:
    reason = outcome
    response = {'error': str(reason)}
    answer(400, response)

```

Here's the output:

```
{"a": 42, "b": 1337} => status: 200 | payload: {'sum': '1379.00'}
{"a": 1.2e3, "b": 1337} => status: 400 | payload: {'error': 'Field "a": Unable to parse "1.2e3" as decimal'}
{"a": 42, "b": "Hello"} => status: 400 | payload: {'error': 'Field "b": Unable to parse "Hello" as decimal'}
{"a": 42, "c": "30"} => status: 400 | payload: {'error': 'At root level: Missing field "b"'}
{"a": 42 "b": "30"} => status: 400 | payload: {'error': "At root level: Invalid JSON, error at line 1, column 10: Expecting ',' delimiter"}
```

### Localizing deserialization errors

It's possible to have jsonbp return localized strings for deserialization
errors. The error instance returned by **deserialize()** on failures
includes a **localize()** method, which takes a list of language codes (ordered
by priority) and attempts to use those languages to generate an error
message explaining the issue.

In the previous example, if we instead changed the last "else" block to:

```py

  else:
    reason = outcome
    localized = reason.localize(['pt_BR', 'it'])
    response = {'error': localized}
    answer(400, response)

```

we would have as output:

```
{"a": 42, "b": 1337} => status: 200 | payload: {'sum': '1379.00'}
{"a": 1.2e3, "b": 1337} => status: 400 | payload: {'error': 'Campo "a": Incapaz de interpretar "1.2e3" como um valor decimal'}
{"a": 42, "b": "Hello"} => status: 400 | payload: {'error': 'Campo "b": Incapaz de interpretar "Hello" como um valor decimal'}
{"a": 42, "c": "30"} => status: 400 | payload: {'error': 'Na raíz: Campo faltando "b"'}
{"a": 42 "b": "30"} => status: 400 | payload: {'error': "Na raíz: JSON inválido, erro na linha 1, coluna 10: Expecting ',' delimiter"}
```

By default, if none of the languages queried in **localize()** are
available, the fallback localization is American English ('en_US'). To use a different
language as fallback, invoke the function **jsonbp.use_default_language** somewhere
in your initialization code with the desired language. For example, the snipped
bellow sets Brazilian Portuguese as the fallback localization:

```py
import jsonbp
jsonbp.use_default_language('pt_BR')
```

### Custom localizations

You can load a custom translation using the method **jsonbp.load_translation()**, which
takes two arguments: the first is the path to the translation file and the second is the language
code that it represents. The calls to this function can be made in your initialization code, and
the localizations will be available throughout the remainder of the program's execution.

The error messages are rather few and can be easily translated should you want to make your own
version. They are composed of a prefix (indicating which level the error happened) followed
by an explanation of what caused it. The messages are specified in a simple properties (ini) file.

For example, here's the full english translation that comes with jsonbp:

```ini
[Messages]
JSON_PARSING=Invalid JSON, error at line {line}, column {column}: {message}
VALUE_PARSING=Unable to decode value as '{type}'
NULL_VALUE=Null value
OUTSIDE_RANGE=Value {value} is outside expected range
INVALID_LENGTH=Length {length} is out of expected range
UNKNOWN_LITERAL=Unknown value
INVALID_ENUM=Value needs to be a string
INVALID_FORMAT=Content is not in the expected format
MISSING_FIELD=Missing field '{field}'
INVALID_ARRAY=Needs to be a list
INVALID_OBJECT=Needs to be an Object

[Prefixes]
FIELD=Field '{assignee}'
OBJECT=Object '{assignee}'
ARRAY=In list '{assignee}' at index {index}
ROOT=At root level

```

## Python serialization

Serialization errors occur when a Python object doesn't fulfill all the required
fields of a schema, or some of the values can't be mapped to the expected type during
a call to the **serialize()** method of Blueprint instances. Generally arising from issues 
in the developer's code, these type of errors simply raises a **jsonbp.SerializationException**
exception, which can be catch and, for instance, logged somewhere for posterior analysis,
returning a 500 status for a client.

## Schema Parsing

These kind of errors are related to issues with the schema itself. They can happen when
calling the **jsonbp.load_file()** or **jsonbp.load_string()** functions. These functions
will throw a **jsonbp.SchemaViolation** exception when the internal parser finds something
that doesn't seem right. Since these errors are intended to the developers themselves
and not to the outside world, their messages are not localized.

For example:
```py
import jsonbp

blueprint = '''
root {
  value: integer (min=dda)
}
'''

try:
  jsonbp.load_string(blueprint)
  print("All good")
	
except jsonbp.SchemaViolation as e:
  print("Something bad occured: " + str(e))
```
would output:
```
Something bad occured: Error parsing line 3: token 'dda' misplaced
```

**Note**: This specific exception is **not really meant to be caught**, that is,
it's not advisable to wrap **load_file()** or **load_string()** calls in a try block
to catch **json.SchemaViolation**. In fact, it is just a means to end execution
immediately and provide feedback why the schema failed to be parsed, but this
should be done during development stage.

In production, once the schema has been correctly written and tested, it seems reasonable
to expect that it won't fail to be parsed anymore, unless the schema file is corrupted somehow.
In this case the best approach might be to let your program fail and check what is stopping
it from starting again.


