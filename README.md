
# jsonbp

**jsonbp** (JSON BluePrint) is a library to validate and deserialize JSON into Python based on a schema (a blueprint). There is [json-schema][json_schema] and its implementations already if you want a more mature and more widely used technique, but I needed some features that were not easily available by just patching json-schema, so this library is the result.

jsonbp's design main goals were:
- schema reuse through import / type system
- support for enums
- built in numeric fixed precision type (which deserializes directly into Python's Decimal)
- built in datetime type (which deserializes directly into Python's datetime)
- error reporting with support for localization

## Schema definition

jsonbp uses its own (very simple) domain language to define a schema.
The only mandatory declaration is the **"root"** entry, which determines the expected JSON contents.
Here's a simple hypotetical example:

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

This defines a schema of an array of minimum length 2 whose elements contain the fields 'x' and 'y' (where both 'x' and 'y' are not allowed to be a negative value plus 'y' not being allowed to be greater than 1) and an optional field 'color' that can be either "RED", "GOLD" or "GREEN". A JSON instance that obeys this schema is:

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

Besides **"root"**, the following directives can be used to organize a schema:
- **"type"** can be thought as a "typedef" in C
- **"node"** can be thought as a "struct" in C
- **"enum"** has the usual meaning

One can then make use of these features and take advantage of a type system. In the monolithic example schema definition above, we could split the parts that can be reused, obtaining, for example:

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

## Usage

And here's how one uses it in code:

```py
import jsonbp

# jsonbp.load()  -> load blueprint from file
# jsonbp.loads() -> load blueprint from string

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

## Requirements

jsonbp requires Python 3.6+, that's it.
Under the hood, jsonbp uses [PLY][ply] for its schema parsing, however PLY comes included with jsonbp already, there's no need to download it separately.

## Documentation

That was just an introduction, if you are interested in using jsonbp here are some more detailed information:
- [`Schema definition`](docs/schema.md) 
- [`Error Handling and Localization`](docs/error.md) 
- [`Examples`](docs/examples.md)

[//]: References
   [json_schema]: <https://json-schema.org/>
   [ply]: <https://www.dabeaz.com/ply/>
   
