
# Error Handling

Errors related to jsonbp can happen at two stages:

- [Errors during Schema Parsing](#errors-during-schema-parsing)
- [Errors during JSON deserialization](#errors-during-json-deserialization)

## Errors during Schema Parsing

This kind of errors are problems with the schema itself. They can happen at
the call to *jsonbp.load()* or *jsonbp.loads()* functions. These functions
will throw a **jsonbp.SchemaViolation** exception when the internal parser
finds something that doesn't seem right. As these errors are to be reported
to the developers themselves and not to the outside world, they do not have
localized messages.

For example:
```py
import jsonbp

blueprint = '''
root {
  value: integer (min=dda)
}
'''

try:
  jsonbp.loads(blueprint)
  print("All good")
	
except jsonbp.SchemaViolation as e:
  print("Something bad occured: " + str(e))
```
would output:
```
Something bad occured: Error parsing line 3: token 'dda' misplaced
```

**Note**: This specific exception is **not really meant to be caught**, that is,
it's not advisable to call loads() or load() from inside a try block and catch
**json.SchemaViolation**. In fact, it is just a means to end execution while
printing the reason why the schema failed to be parsed, but this should be
done during development stage. In production, after the schema has correctly
been written and tested, it seems reasonable that it won't fail to be parsed anymore,
unless the schema file is corrupted somehow, in which case the best approach
might be to let your program fail and check what is stopping it from starting again.

## Errors during JSON deserialization

These errors happen when someone feeds your program a JSON that is either
incomplete or that has an unexpected/undesired value. The blueprint
method **deserialize()** returns a pair of values, the first one indicates
whether the deserialization was successful or not. If deserialization fails,
the seconds value holds a message explaining why the given string was not accepted.

Here's a full example ilustrating error reporting: we define a blueprint to accept
fields **'a'** and **'b'** that must be stricly decimal. We then do some processing
on them and return the result with status 200 (success). If, however, a bad JSON
is fed to our program, we return status 400 (bad request) and the reason of the failure:

```py
import jsonbp

#------------------------------------

blueprint = '''
root {
  a: decimal,
  b: decimal
}
'''

blueprint = jsonbp.loads(blueprint)

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

### Localizing JSON deserialization Errors

It's possible to make jsonbp return localized strings from errors of
deserialization. To do that, right after importing the jsonbp module, use its
function **useLanguage()** to set the desired localization. American English
('en_US') is the default and also the fallback if the desired language is
not found.

To use Brazilian Portuguese for example, one can do as follows during importing:

```py
import jsonbp
jsonbp.useLanguage('pt_BR')
```

and then the previous example would have as output:

```
{"a": 42, "b": 1337} => status: 200 | payload: {'sum': '1379.00'}
{"a": 1.2e3, "b": 1337} => status: 400 | payload: {'error': 'Campo "a": Incapaz de interpretar "1.2e3" como um valor decimal'}
{"a": 42, "b": "Hello"} => status: 400 | payload: {'error': 'Campo "b": Incapaz de interpretar "Hello" como um valor decimal'}
{"a": 42, "c": "30"} => status: 400 | payload: {'error': 'Na raíz: Campo faltando "b"'}
{"a": 42 "b": "30"} => status: 400 | payload: {'error': "Na raíz: JSON inválido, erro na linha 1, coluna 10: Expecting ',' delimiter"}
```

jsonbp first searchs the working directory for the file **messages.\<language code>.ini**.  
If no such file exists in the working directory, it then searchs for the same
file name inside directory **jbp/localization** where jsonbp is installed.

The messages are rather few and can be easily translated should you want to make your own version.  
They are composed of a prefix (signalizing which level the error happened) plus an explanation
of what caused it. The messages are specified in a simple properties (ini) file.

For example, here's the english version that comes with jsonbp:


```ini
[Messages]
JSON_PARSING=Invalid JSON, error at line {line}, column {column}: {message}
NULL_VALUE=Null value
INTEGER_PARSING=Unable to parse "{text}" as integer
FLOAT_PARSING=Unable to parse "{text}" as float
DECIMAL_PARSING=Unable to parse "{text}" as decimal
OUTSIDE_RANGE=Value {value} is outside expected range
INVALID_BOOLEAN=Value must be "true" or "false", got "{value}"
INVALID_STRING=Not a valid string
INVALID_LENGTH=Length {length} is out of expected range
INVALID_DATETIME="{text}" does not match expected datetime format or is not a valid date
UNKNOWN_LITERAL=Unknown value "{value}"
INVALID_ENUM=Not a valid string
MISSING_FIELD=Missing field "{field}"
INVALID_ARRAY=Needs to be a list
INVALID_NODE=Needs to be an Object

[Prefixes]
FIELD=Field "{assignee}":
NODE=Node "{assignee}":
ARRAY=In list "{assignee}" at index {index}:
ROOT=At root level:

```

