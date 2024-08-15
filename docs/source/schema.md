# Schema Directives

A jsonbp schema can be composed of the following directives:

- [object](#object)
- [type](#derived-types)
- [enum](#enums)
- [root](#root)
- [import](#import)

Comments are done using the sharp (#) character

```
# This is a comment
# and this as well
```

## Objects

Objects denote compound structures composed of **fields**, which are named
entries assigned to hold exclusively certain types and specializations.
To register one type of object, jsonbp accepts the pattern:

```
object <object name> {
  <field declaration>,
  <field declaration>,
  ...
  <field declaration>
}
```

where field declarations are separated by a comma.
Field declaration themselves are composed of a field name followed by its type
separated by a colon:

```
<field name> : <field type>
```

Field types can be simple types (primitive or derived types), enums, objects
or even arrays of those. For example:

```
object car {
  model: string,
  brand: string,
  year: integer
}
```

Objects can be nested. The "car" object above could be used in a
"car_sale" object declaration, like this:

```
object car_sale {
  description: car,
  price: decimal,
  discount: decimal,
  installments: integer
}
```

Nesting can also appear as an inline definition. That is, it's not strictly
necessary to register an object beforehand in order to use it in the middle of
another object's definition (if that is the only place that it occurs, for example).
The "car" example above could very well be defined like the following:

```
object car_sale {
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

By default every field in an object is mandatory. Thus, if any field is not
present in the JSON string being deserialized or in the Python object being
serialized, an error will be flagged. If a field is to be optional, just prefix
the field definition with the **"optional"** directive, like this:

```
object address {
  street: string,
  number: integer,
  zipCode: string,
  optional complement: string
}
```

Optional fields, when present, must obey the type and specialization defined for them.
Also, by default, no fields can be assigned null values. To allow specific fields to be allowed
null values, prefix it's type as **nullable**, like this:

```
object order {
  itemId: integer,
  value: decimal,
  shipping: nullable address
}

```

> **_NOTE:_** An optional nullable field is thus the most liberal definition a field can have.
In this case, the field may or may not be present in either the JSON instance (deserialization)
or in the Python object (serialization), and if present, it can also be null.

Objects can be extended, which means you can define a new object type based on an
existing one. It'll inherit all the fields defined in its parent or that the parent itself
inherited. It's not possible, however, to redefine fields using the same field name in
child objects that are already present in any of its ancestors, an error will happen during
schema parsing if you inadvertently do that. The syntax is as follows:

```
object <child object name> extends <parent object name> {
  <new field declaration>,
  <new field declaration>,
  ...
}
```

For example:

```
object point2d {
  x: float,
  y: float
}

object point3d extends point2d {
  z: float
}
```

## Derived types

It's possible to register and reuse the specialization of a primitive type. This is done by
the **type** directive, which creates a **derived type** that retains all the specificities
that were defined. This directive has the following syntax:

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

object values {
  increase: percent,
  cosine: normalized
}
```

When registering a new derived type, it's possible to change previously defined specificities.
This means you can alter some or all the specificities already defined in a base type,
be it during the declaration of a new type as well directly in the field declaration,
like in the following scenario:

```
type broadScale : float (min=0, max=999)
type narrowScale : broadScale (max=99)

object scaled {
  restrictedScale : narrowScale (max=9)
}
```


## Enums

Enums can be employed to define types whose values are part of a limited set. They
need to be JavaScript **string** and will be deserialized into Python's **str** and vice
versa. As one might expect, if some enum field during serialization/deserialization holds a value
that is not present in the set of values allowed of an enum, an error will be flagged.
Note that values in enums are **case sensitive**. Enums can be registered through the
**"enum"** directive:

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

And just like objects, their definition can be inlined:

```
object sale {
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

**root** defines the contents that need to be present in an JSON string for it to be
validated and further deserialized, and conversely, the contents that need to be present
in a Python object for it to be serialized. The **root** directive can receive a simple type,
an enum or an object, either through a named type or an inline definition:

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
object credentials {
  username: string(minLength=3),
  password: string(minLength=8)
}

root credentials
```

Only one root can be declared by schema file. Declaring two or more roots
will characterize a schema as ambiguous and jsonbp will complain during
schema parsing.

## Import

Schema files can be imported by other schema files in order to reuse the
definions present in them. The syntax is:

```
include <path to schema file inside quotes including extension>
```

The search path is relative to the schema file that has the "import" directive.  
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

Caveats during imports:
- **root** directives (if present) are ignored when their schema file is imported.
- When loading a schema from a string, the execution path is used as base path
- If the same type name is defined in more than one schema (be it a simple
type, an enum or an object), jsonbp will complain and throw an error during
schema parsing. However, a single schema can be imported from multiple schemas
with no problem (internally jsonbp stores the full paths that have been
imported, and won't even load the same file twice)

