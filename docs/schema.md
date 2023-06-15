# Contents

- [Primitive Types](#primitive-types)
- [Schema Directives](#schema-directives)
- [Arrays](#arrays)

# Primitive Types

These are the primitive types that jsonbp accepts and the corresponding Python
types that they map to:

| jsonbp   | Python |
| ------   | ------ |
| integer  | int |
| float    | float |
| decimal  | decimal.Decimal |
| bool     | bool |
| datetime | datetime.datetime |
| string   |  str |

When used in a field declaration, simple types can be customized through
**specificities**, which is a list of key-values enclosed in parenthesis and
separated by commas. Each type has a fixed and well defined list of possible
specificities.

For example:
```
node weekInstant {
  hours: integer (min=0, max=12),
  minutes : integer (min=0, max=59),
  seconds : integer (min=0, max=59),
  timezone: string (minLength=3, maxLength=3),
  DST: bool (coerce=false)
}
```

The following is a list of all possible specificities by primitive type:

| type | specificity | Default |
| ------   | ------ | ------   |
| integer  | min<br>max | -2,147,483,648<br>+2,147,483,647 |
| float  | min<br>max | -infinity<br>+infinity |
| decimal | fractionalLength<br>min<br>max<br>decimalSeparator<br>groupSeparator | 2<br>-2,147,483,648.00<br>+2,147,483,648.00<br>'.' (dot)<br>'' (empty string) |
| bool | coerce | false |
| datetime | format | "%Y-%m-%d %H:%M:%S" |
| string | minLength<br>maxLength | 0<br>1024 |

Some of the specificities may warrant an explanation:

**decimal**   
*fractionalLength*: Number of digits after the radix  
*decimalSeparator*: Character that represents the radix  
*groupSeparator*: Character used to organize and simplify reading big numbers  

**bool**   
*coerce*: If false, only **true** and **false** are acceptable booleans,
otherwise (if "coerce" is true) during deserialization, truthy values will
be accepted as **true** and falsy values will be accepted as **false**.

**datetime**   
*format*: Format used for datetime parsing. It'll be directy fed to strptime():  
[https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior)

# Schema Directives

A jsonbp schema can be composed of the following directives:

- [node](#nodes)
- [type](#derived-types)
- [enum](#enums)
- [root](#root)
- [import](#import)

Comments are done using the sharp (#) character

```
# This is a comment
# and this as well
```

## Nodes

Nodes denote Objects in JavaScript. They are composed of **fields**, named
entries which are assigned to hold exclusively a certain type and
specialization. To register a kind of node, jsonbp accepts the pattern:

```
node <node name> {
  <field declaration>,
  <field declaration>,
  ...
  <field declaration>
}
```

Where a field declaration is composed of a field name and its type
separated by a colon. Fields of a node are separated by a comma:

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

Nodes can be nested. The "car" node above could be reutilized in a
"car_sale" node, like this:

```
node car_sale {
  description: car,
  price: decimal,
  discount: decimal,
  installments: integer
}
```

They can also have an "inline" definition, that is, it's not strictly
necessary to register a node directive before using it. The
car example above could very well be defined like:

```
node car_sale {
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

By default every field in a node is mandatory. Thus, if any field is not
present in the JSON instance being deserialized, an error will be flagged.
If a field is to be optional, just prefix the field definition with
the **"optional"** directive, like this:

```
node address {
  street: string,
  number: integer,
  zipCode: string,
  optional complement: string
}
```

Optional fields, when present, must obey the type and specialization defined for them.

Nodes can also be extended. You can create a new node based on a previously defined one.
It'll inherit all the fields defined in its parent or that the parent itself inherited. 
t's not possible, however, to "redefine" fields using the same field name in child nodes
that are already present in any of their parents, an error will happen during
schema parsing if you inadvertently do that. The syntax is as follows:

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

## Derived types

It's possible to register and reuse the specialization of a type. This is done by
the **type** directive, which creates a **derived type** that withholds all the specificities
defined for it. This directive has the following syntax:

```
type <derived type> : <parent type> (<specificity>, <specificity>, ...)
```

Derived types can be a further specialization of an already derived type.
Once defined, a derived type can be used do specify a field content just like
a primitive type. For example:

```
type percent : decimal (min=0.00, max=100.00)
type unitRange : double (min=-1, max=+1)
type normalized : unitRange (min=0)

node values {
  increase: percent,
  cosine: normalized
}
```

When registering a new derived type, one can alter previously defined specificities.
This means you can alter some or all the specificities already defined in a base type,
be it during the declaration of a new type as well directly in the field declaration,
like in the following scenario:

```
type broadScale : float (min=0, max=999)
type narrowScale : broadScale (max=99)

node scaled {
  restrictedScale : narrowScale (max=9)
}
```


## Enums

Enums can be employed to define types whose values are part of a limited set. They
need to be JavaScript **strings** and will be deserialized into Python's **str**. As
one might expect, if the value in an JSON instance being deserialized is not present
in the set of values of an enum, an error will be flagged. Note that values in enums
are **case sensitive**. Enums can be registered through the **"enum"** directive:

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

And just like nodes, they can be inlined:

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

**root** is the only mandatory directive that needs to be present in a blueprint
(unless a schema file is only meant to be imported, as it's explained later on).
It defines the contents that need to be present in an JSON instance for it to be
validated and further deserialized. The "root" directive can receive a simple type,
an enum or a node, either through a named type or a just in place definition:

Example 1
```
root integer
```

Example 2
```
root string (maxLength=128)
```

Example 3
```
root { IDLE, BUSY }
```

Example 4
```
root {
  username: string(minLength=3),
  password: string(minLength=8)
}
```

Example 5
```
node credentials {
  username: string(minLength=3),
  password: string(minLength=8)
}

root credentials
```

Only one root can be declared by schema file. Declaring two or more roots
will characterize a schema as ambiguos and jsonbp will complain during the
schema parsing.

## Import

Schema files can be imported by other schema files in order to reuse the
definions present in them. The syntax is:

```
include <path to schema file inside quotes including extension>
```

The path is relative to the schema file that has the "import" directive.  
So, for example, if we have this file structure:

```
.
|-> schema00.jbp
|-> schema01.jbp
|
|-> dir1
|    |-> schema10.jbp
|    '-> schema11.jbp
|
'-> dir2
     |-> schema20.jbp
     '-> schema21.jbp
```

The following imports are all valid:

- Inside **schema00.jpb**
```
import "schema01.jbp"
import "dir1/schema10.jbp"
import "dir2/schema21.jbp"
```

- Inside **dir1/schema11.jbp**
```
import "../schema00.jbp"
import "schema10.jbp"
import "../dir2/schema20.jbp"
```

When loading a schema from a string, the execution path is used as base path
instead. "root" directives (if present) are ignored when their schema file is
imported.

If the same type name is defined in more than one schema (be it a simple
type, an enum or a node), jsonbp will complain and throw you an error during
schema parsing. However, a single schema can be imported from multiple schemas
with no problem (internally jsonbp stores the full paths that have been
imported, and won't even load the same file twice)

# Arrays

To make any field an array, just add brackets "[]" at the end of its
definition. The field can be either a simple type, an enum or a node.
During deserialization, jsonbp will check if the value is in fact an **Array**,
even a empty one, and will reject the JSON instance otherwise. If it is
correctly validated by jsonbp, the result will be a Python **list**.
For example:

```
node point2d {
  x: float,
  y: float
}

root {
  points: point2d[],
  deltaTs: double (min=0.0) [minLength=2],
  conditions: {
    GOOD,
    REGULAR,
    BAD,
    REJECTED
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

As is ilustrated by the above examples, arrays can have two "specificities",
**minLength** and **maxLength**, which limits respectively the minimum and
maximum number of elements the array may contain.
