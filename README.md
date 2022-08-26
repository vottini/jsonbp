
# jsonbp

**jsonbp** (JSON BluePrint) is a library to validate and deserialize JSON into Python based on a schema. There is [json-schema][json_schema] and its implementations already if you want a more mature and more widely used technique, but I needed some features that were not easily available by just patching json-schema, so this library is the result.

jsonbp's design main goals were:
- schema reuse through import / type system
- support for enums
- built in numeric fixed precision type (which deserializes directly into Python's Decimal)
- built in datetime type (which deserializes directly into Python's datetime)
- error reporting with support for localization
- easy to integrate and use

## Contents
 - [Schema definition](#schema-definition)
 - [Usage](#usage)
 - [Requirements and Dependencies](#requirements-and-dependencies)
 - [Installation](#installation)
 - [Documentation](#documentation)

## Schema definition

jsonbp uses its own (very simple) domain language to define a schema.
The only mandatory declaration is the **"root"** entry, which determines the expected JSON contents.
Here's a simple hypothetical example:

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

This defines a schema of an array of minimum length 2 whose elements contain the fields 'x' and 'y' (where both 'x' and 'y' are not allowed to be a negative value plus 'y' not being allowed to be greater than 1.0) and an optional field 'color' that can be either "RED", "GOLD" or "GREEN". A JSON instance that obeys this schema is:

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

Besides **"root"**, in jsonbp the following optional directives can be used to organize a schema:
- **"type"** -> to define specialized (restricted) simple types
- **"node"** -> to specify the contents of compound types (Objetcs)
- **"enum"** -> to define a list of allowed values for given fields
- **"import"** -> to reuse directives from existing blueprints

One can then make use of these features to simplify and make the schema more modular. In the above example schema, we could split the definitions and get something more reusable, like the following:

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

where the contents of file "color.jbp" would then be:

```
enum color {
	RED,
	GOLD,
	GREEN
}
```

(For detailed information using these directives, see the [Documentation section](#documentation))

## Usage

All of jsonbp can be summarized in only 2 entrypoints which are suplied by 3 functions:

### Schema parsing

- jsonbp.load(\<schema file path>) => \<blueprint object>
- jsonbp.loads(\<schema string>) => \<blueprint object>

For schema loading one can use these two functions, which do the same thing, the only difference is that one expects a path to a file storing the schema content while the other expects a string with the schema content itself. When there's a problem with the supplied schema, an exception is thrown. More on this can be read on [`Error handling and error localization`](docs/error.md). Both functions, when succeed loading the schema, return a blueprint instance that can be used to deserialize JSON strings.

### JSON deserialization

- \<blueprint object>.deserialize(\<JSON string>) => (success, outcome)

This is the only method that should be invoked from the blueprint object returned by load()/loads(). It expects a string holding the JSON contents to be deserialized. It returns a tuple in the form *(success, outcome)*. **success** is a boolean flagging if the deserialization was successful. If successful, **outcome** will store the Python data obtained from the JSON string. Otherwise (**success** is false) **outcome** will have a message explaining what was not compliant with the expected schema.

### Example

Here's how one uses these functions in code:

```py
import jsonbp

blueprint = jsonbp.loads('''
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

## Requirements and Dependencies

jsonbp requires Python 3.6+, that's it.  
Under the hood, jsonbp uses [PLY][ply] for its schema parsing. PLY comes included with jsonbp already, there's no need to download it separately.

## Installation

jsonbp is available at PyPI:  [https://pypi.org/project/jsonbp/](https://pypi.org/project/jsonbp/)

To install through pip:
```bash
pip3 install jsonbp
```

## Documentation

That was just an introduction, if you are interested in using jsonbp here are some more detailed information:
- [`Schema definition`](docs/schema.md)
- [`Error handling and error localization`](docs/error.md)
- [`Sample of using jsonbp in Flask`](https://github.com/vottini/sample-jsonbp-flask)

[//]: References
   [json_schema]: <https://json-schema.org/>
   [ply]: <https://www.dabeaz.com/ply/>
   
