
## General Structure

## Nodes

Nodes denote Objects in javascript. They are composed of **'fields'**, named entries which are assigned to hold exclusively certain types. To register a kind of node, jsonbp accepts the pattern:

node <node name> {
	<field declaration>,
	<field declaration>,
	...
	<field declaration>
}

Where a field declaration is composed of a field name and its type separated by a colon. Fields of a node are separated by a comma:

<field name> : <field type>

for example:

node car {
	model: string,
	brand: string,
	year: integer
}

Nodes can be nested. The "car" node above could be reutilized in a "car_sale" node, like this:

car_sale {
	description: car,
	price: decimal,
	discount: decimal,
	installments: integer
}

They can also be defined ad hoc, they don't need to be registered beforehand. The car example above could very well be defined like:

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

By default, every field in a node is mandatory. Thus, if any field is not present in the JSON being deserialized, a deserialization error will be flagged. If a field is to be optional, just prefix the field definition with the **"optional"** keyword, like this:

node address {
	street: string,
	number: integer,
	zipCode: string,
	optional complement: string
}

Optional fields, when present, must obey the type defined for them.

Nodes can be extended. That is, you can create a new node based on a previously defined one. It'll inherit all the fields defined in its parent or that the parent itself inherited. While extending a node one can evidently add new fields. It's not possible, however, to "redefine" fields using the same field name in child nodes that are present in their parents, an error will be thrown if you attempt to do that. The syntax is as follows:

node <child node name> extends <parent node name> {
	<new field declaration>,
	<new field declaration>,
	...
}

For example:

node point2d {
	x: float,
	y: float
}

node point3d extends point2d {
	z: float
}

## Primitive types

## Specialized types

## Enums

## Root

## How to array

## Include
