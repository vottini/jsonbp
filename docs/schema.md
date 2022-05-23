
## General Structure

A jsonbp schema can be composed of the following declarations:

- node
- type
- enum
- root 

## Nodes

Nodes denote Objects in javascript. They are composed of **'fields'**, named entries which are assigned to hold exclusively certain types. To register a kind of node, jsonbp accepts the pattern:

```
node <node name> {
	<field declaration>,
	<field declaration>,
	...
	<field declaration>
}
```

Where a field declaration is composed of a field name and its type separated by a colon. Fields of a node are separated by a comma:

```
<field name> : <field type>
```

for example:

```
node car {
	model: string,
	brand: string,
	year: integer
}
```

Nodes can be nested. The "car" node above could be reutilized in a "car_sale" node, like this:

```
car_sale {
	description: car,
	price: decimal,
	discount: decimal,
	installments: integer
}
```

They can also be defined just in place, it's not necessary to register them using the "node" directive beforehand. The car example above could very well be defined like:

```
car_sale {
	description: {
		model: string,
		brand: string,
		year: integer
	},

	price: decimal,
	discount: decimal,
	installments: integer
}
```

By default, every field in a node is mandatory. Thus, if any field is not present in the JSON instance being deserialized, an error will be flagged. If a field is to be optional, just prefix the field definition with the **"optional"** directive, like this:

```
node address {
	street: string,
	number: integer,
	zipCode: string,
	optional complement: string
}
```

Optional fields, when present, must obey the type defined for them.

Nodes can also be extended. That is, you can create a new node based on a previously defined one. It'll inherit all the fields defined in its parent or that the parent itself inherited. It's not possible, however, to "redefine" fields using the same field name in child nodes that are already present in any of their parents, an error will be thrown if you attempt to do that. The syntax is as follows:

```
node <child node name> extends <parent node name> {
	<new field declaration>,
	<new field declaration>,
	...
}
```

For example:

```
node point2d {
	x: float,
	y: float
}

node point3d extends point2d {
	z: float
}
```

## Primitive types

These are the primitive types that jsonbp accepts and the corresponding Python types that they map to:

| jsonbp   | Python |
| ------   | ------ |
| integer  | int |
| float    | float |
| decimal  | decimal.Decimal |
| bool     | bool |
| datetime | datetime.datetime |
| string   |  str |

When used in a field declaration, primitive types can be customized through specificities, which is a list of pair-values enclosed in parenthesis and separated by commas. Each type has a fixed and well defined list of possible specificities.

For example:
```
node weekInstant {
    weekday: string (minLength=3, maxLength=3),
    hours: integer (min=0, max=12),
    minutes : integer (min=0,max=59),
    seconds : integer (min=0,max=59),
    ampm: string (minLength=2, maxLength=2)
}
```

And the following is a list of all possible specificities by primitive type:

| type | specificity | Default |
| ------   | ------ | ------   |
| integer  | max<br>min | 4,294,967,296<br>-4,294,967,296 |
| float  | max<br>min | +infinity<br>-infinity |

## Specialized types


## Enums

## Root

## How to array

## Include
