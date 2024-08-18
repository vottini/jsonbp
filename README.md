
# jsonbp

[![Documentation Status](https://readthedocs.org/projects/jsonbp/badge/?version=latest)](http://jsonbp.readthedocs.io/?badge=latest)
[![codecov](https://codecov.io/github/vottini/jsonbp/graph/badge.svg?token=N2H2WJ0SC5)](https://codecov.io/github/vottini/jsonbp)

**jsonbp** (JSON BluePrint) is a library for serializing and deserializing JSON
to and from Python based on schemas. While [json-schema][json_schema] and its
implementations offer a more mature and widely used technique, a different
approach was desired, which led to the development of this library.

jsonbp's design main goals were:
- schema reuse through import / type system
- custom user definable primitive types
- built in numeric fixed precision type which deserializes into Python's Decimal
- built in datetime type which deserializes into Python's datetime
- error reporting with support for localization
- support for enums
- easy to integrate and use

## Brief Introduction
 - [Schema definition](#schema-definition)
 - [Usage](#usage)
 - [Requirements and Dependencies](#requirements-and-dependencies)
 - [Installation](#installation)
 - [Documentation](#documentation)

## Schema definition

jsonbp uses its own (very simple) domain language to define a schema.
Here's a simple example:

```
root {
  x: float (min=0.0),
  y: float (min=0.0, max=1.0),

  optional color: {
    RED,
    GOLD,
    GREEN
  }
} [minLength=2]
```

This defines a schema that represents an array of minimum length 2 whose
elements contain the fields 'x' and 'y', where both 'x' and 'y' are not
allowed to be negative and further 'y' is not allowed to be greater than 1.0.
An optional field 'color' can also exist, and if present it needs to be either
"RED", "GOLD" or "GREEN". A JSON instance that obeys this schema is thus:

```js
[
  {
    "x": 2.0,
    "y", 0.004,
    "color": "RED"
  },

  {
    "x": 3.0,
    "y", 0.009
  },

  {
    "x": 4.0,
    "y", 0.016,
    "color": "GREEN"
  }
]
```

jsonbp offers the following directives to organize a schema:
- **"root"** -> defines which type will correspond to some JSON
- **"type"** -> defines specialized (restricted) simple types
- **"object"** -> specifies the contents of compound types (Objects)
- **"enum"** -> defines a list of allowed values for a given field
- **"import"** -> reuses directives from existing blueprints

These structures can be employed to simplify and make the schema more
modular. In the above example, one could split the definitions and get
something more reusable, like the following:

```
type non_negative : float (min=0.0)
type normalized : non_negative (max=1.0)

node coordinates {
  x: non_negative,
  y: normalized
}

include "color.jbp"
node colored_coordinates extends coordinates {
  optional color: color
}

root colored_coordinates[minLength=2]
```

where the contents of file "color.jbp" would be:

```
enum color {
  RED,
  GOLD,
  GREEN
}
```

> **_NOTE:_**  For full documentation, see [Documentation](#documentation)

## Usage overview

### Schema parsing

- jsonbp.load\_file(blueprint\_path: str) => JsonBlueprint
- jsonbp.load\_string(blueprint\_string: str) => JsonBlueprint

### JSON deserialization

- JsonBlueprint.deserialize(contents: str) => (success: bool, outcome: object)
- JsonBlueprint.serialize(payload: object) => str

### Example

```py
import jsonbp

blueprint = jsonbp.load_string('''
root {
  success: {
    YES,
    NO
  }
}
''')

jsonInstance = '{ "success": "YES" }'
success, outcome = blueprint.deserialize(jsonInstance)
print(f'Success: {success}')
print(f'Outcome: {outcome}')
```

Output:

```
Success: true
Outcome: {"success":"YES"}
```

> **_NOTE:_**  For full documentation, see [Documentation](#documentation)

## Requirements and Dependencies

jsonbp requires Python 3.7+, that's it.
Under the hood, jsonbp uses [PLY][ply] for its schema parsing. PLY comes
included with jsonbp already, there's no need to download it separately.

## Installation

jsonbp is available at PyPI:  [https://pypi.org/project/jsonbp/](https://pypi.org/project/jsonbp/)

To install through pip:
```bash
pip install jsonbp
```

## Documentation

- [`Full documentation`](https://jsonbp.readthedocs.io/en/latest/)
- [`Sample of using jsonbp in Flask`](https://github.com/vottini/sample-jsonbp-flask)

[//]: References
   [json_schema]: <https://json-schema.org/>
   [ply]: <https://www.dabeaz.com/ply/>

