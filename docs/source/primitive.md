# Primitive Types

## Built-in primitive types

These are the built-in primitive types accepted by jsonbp and the corresponding Python
types that they map to:

| jsonbp   | Python |
| ------   | ------ |
| Integer  | int |
| Float    | float |
| Decimal  | decimal.Decimal |
| Bool     | bool |
| instant | datetime.datetime |
| String   |  str |

When used in declarations, primitive types can be customized through
**specificities**, which are a list of key-value pairs enclosed in parenthesis and
separated by commas. Each type has a fixed and well defined list of possible
specificities.

For example:
```
object weekInstant {
  hours: Integer (min=0, max=12),
  minutes : Integer (min=0, max=59),
  seconds : Integer (min=0, max=59),
  timezone: String (minLength=3, maxLength=3),
  DST: Bool (coerce=false)
}
```

The following is a list of all possible specificities by primitive type:

| type | specificity | Default |
| ------   | ------ | ------   |
| Integer  | min<br>max | -2,147,483,648<br>+2,147,483,647 |
| Float  | format<br>atLeast<br>atMost<br>greaterThan<br>lessThan<br>allowNaN<br> | %g<br>-infinity<br>+infinity<br>NaN<br>NaN<br>false |
| Decimal | precision<br>min<br>max<br>radix<br>separator<br>indianFormat<br>prefix<br>suffix | 2<br>-2,147,483,648.00<br>+2,147,483,648.00<br>. (dot)<br>(empty string)<br>false<br>(empty string)<br>(empty string) |
| Bool | coerce | false |
| Instant | iso<br>isoResolution<br>format | true<br>milliseconds<br>%Y-%m-%dT%H:%M:%S%z |
| String | minLength<br>maxLength<br>format | 0<br>1024<br>.* |

Some of the specificities may warrant an explanation:

**Float**
*atLeast* and *atMost*: Defines closed intervals
*greaterThan* and *lessThan*: Defines open intervals
*format*: Format for serializing floats in a desired way. [More Info](https://docs.python.org/3/library/string.html#format-specification-mini-language)

**Decimal**
*precision*: Number of digits after the radix
*radix*: Character that represents the radix
*separator*: Character used to organize and simplify reading large numbers
*indianFormat*: Whether to use the indian numbering system
*prefix*: Leading text to strip during deserialization or add during serialization
*suffix*: Trailing text to strip during deserialization or add during serialization

**Bool**
*coerce*: If set to false, only **true** and **false** are acceptable boolean values.
Otherwise (if "coerce" is true) during deserialization, truthy values will
be accepted as **true** and falsy values will be accepted as **false**.

**Instant**
*iso*: Whether to use ISO 8601 format or not
*isoResolution*: When *iso* is true, defines which resolution to use. Possible values can be found [here](https://docs.python.org/3/library/datetime.html#datetime.datetime.isoformat)
*format*: Defines which format to use when *iso* is false. The format will be directy passed to
[strftime() and strptime()](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior)

**String**
*format*: Regular expression defining the pattern a string must conform to in order to be accepted as valid input.

## Custom primitive types

It's possible to load and use custom primitive types or even overwrite the builtin ones offered by jsonbp.
This can be achieved writing a Python script with a dictionary named **type_specs** in which the following
fields need to be defined:

**name**: name of the primitive type
**parser**: function that receives a string and the specificities, validates its contents, and returns
deserialized Python data
**formatter**: function that receives a Python data and the specificities, validates its contents,
and returns a string
**defaults**: dictionary with the specificities allowed for the type and its default values

*parser* and *formatter* functions should return a tuple in the form *(success, outcome)* where **success**
indicates whether the operation succeed. If **success** is true, outcome needs to be the resulting
value. If **success** is false, outcome should be a dictionary with the following contents:

**error**: type of error that was caught
**context**: dicionary holding the context with the values which led to the error

The possible errors types are exported in **jsonbp.ErrorType**.
They are listed below:

| ErrorType | Context |
| ------   | ------ |
| JSON_PARSING     | line, column, message |
| VALUE_PARSING    | type                  |
| NULL_VALUE       | field                 |
| OUTSIDE_RANGE    | value                 |
| INVALID_LENGTH   | length                |
| UNKNOWN_LITERAL  |                       |
| INVALID_ENUM     |                       |
| INVALID_FORMAT   |                       |
| MISSING_FIELD    | field                 |
| INVALID_ARRAY    |                       |
| INVALID_OBJECT   |                       |

If an exception is raised and propagates from either *parser()* or *formatter()*, it'll be caught and a
VALUE_PARSING error will be flagged with **type** in the context indicating the name of the primitive type.
For example, the following code defines a primitive type that only accepts even integers:

```py
import jsonbp

def _format(value, specs):
  return str(value)


def _parse(value, specs):
  intValue = int(value)
  if intValue % 2 != 0:
    return False, {
      "error": jsonbp.ErrorType.OUTSIDE_RANGE,
      "context": {"value": intValue}
    }

  return True, intValue


type_specs = {
  'name': 'Even',
  'parser': _parse,
  'formatter': _format,
  'defaults': dict()
}

```

All jsonbp builtin types are defined in this way, and their source can be consulted for further reference.
To actually make these custom types available, the functions **jsonbp.load_string()** and **jsonbp.load_file()**
accept the named argument **custom_types**, which should be a list of directories to scan for extra primitive
type definitions. If a custom primitive type has the same name as one of the builtin
primitive types, it'll override its original definition and display a warning in the terminal, which you
can safely ignore if that is your intention.

