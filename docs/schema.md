
## General Structure

A jsonbp schema can be composed of the following declarations:

- node
- type
- enum
- root

To add comments to a schema, use the sharp (#) character

```
# This is a comment
# and this as well
```

## Nodes

Nodes denote Objects in javascript. They are composed of **fields**, named entries which are assigned to hold exclusively certain types. To register a kind of node, jsonbp accepts the pattern:

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

When used in a field declaration, primitive types can be customized through **specificities**, which is a list of key-values enclosed in parenthesis and separated by commas. Each type has a fixed and well defined list of possible specificities.

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

The following is a list of all possible specificities by primitive type:

| type | specificity | Default |
| ------   | ------ | ------   |
| integer  | min<br>max | -2,147,483,648<br>2,147,483,647 |
| float  | min<br>max | -infinity<br>+infinity |
| decimal | fractionalLength<br>min<br>max<br>decimalSeparator<br>groupSeparator | 2<br>-2,147,483,648.00<br>+2,147,483,648.00<br>'.' (dot)<br>'' (empty string) |
| bool | coerce | false |
| datetime | format | "%Y-%m-%d %H:%M:%S" |
| string | minLength<br>maxLength | 0<br>1024 |

Some of the specificities need an explanation:

**decimal**
*fractionalLength*:
*decimalSeparator*:
*groupSeparator*:

**bool**
*coerce*:

**datetime**
*format*:

## Derived types

It's possible to register and reuse the specialization of a type. This is done by the **type** directive, which creates a **derived type** that applies inherently all the specificities defined for it. This directive has the following syntax:

```
type <derived type> : <parent type> (<specificity>, <specificity>, ...)
```

Derived types need not be based solely on primitive types, they can be a further specialization of an already derived type. Once defined, a derived type can be used do specify a field content just like a primitive type. For example:

```
type percent : decimal (min=0.00, max=100.00)
type unitRange : double (min=-1, max=+1)
type normalized : unitRange (min=0)

node values {
    increase: percent,
    cosine: normalized
}
```

## Enums

Enums can be employed to define types that hold discrete and limited values. They need to be javascript **strings** and will be deserialized into Python's **str**. As one might expect, if the value in an instance being deserialized is not present in the enum list, an error will be flagged. Note that values in enums are **case sensitive**. Enums can be registered through the **"enum"** directive:

```
enum months {
	January,
	February,
	March,
	April,
	May,
	June,
	July,
	August,
	September,
	October,
	November,
	December
}
```

And like nodes, they can be defined just in place:

```
node sale {
	amount: decimal (min=0.00),
	status: {
		AWAITING,
		PAID,
		REJECTED,
		CANCELLED
	}
}
```

## Root

**"root"** is the only mandatory directive that needs to be present in a blueprint (unless a schema file is only meant to be imported, as it's explained later on). It defines the contents that need to be present in an JSON instance for it to be validated and further deserialized. The "root" directive can receive a simple type, an enum or a node, either through a registered identifier or defined just in place:

```
root integer

# or

root string (maxLength=128)

# or

root { IDLE, BUSY }

# or

root {
	username: string(minLength=3),
	password: string(minLength=8)
}

# or

node credentials {
	username: string(minLength=3),
	password: string(minLength=8)
}

root credentials

```

Only one root can be declared. Declaring two or more roots will characterize a schema as ambiguos and jsonbp will complain during the schema parsing.


## Array

To make any field an array, just add brackets "[]" at the end of its definition. The field can be either a simple type (primitive or derived), an enum or a node. During deserialization, jsonbp will check if the value is in fact an **Array**, even a empty one, and will reject the JSON instance otherwise. If it is correctly validated by jsonbp, the result will be a Python **list**.  For example:

```
node point2d {
	x: float,
	y: float
}

root {
	points: point2d[],
	deltaTs: double (min=0.0) [minLength=2],
	conditions: {
		"GOOD",
		"REGULAR",
		"BAD",
		"REJECTED
	} [minLength=1, maxLength=3]
}
```

"root" itself can also be an array:

```
root {
	APPLE,
	ORANGE,
	STRAWBERRY,
	PINEAPLE
} [minLength=2, maxLength=2]

# or even

root point2d[]
```

## Include
