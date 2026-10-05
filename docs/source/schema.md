# Schema Directives

A jsonbp schema can be composed of the following directives:

- [object](#object)
- [type](#derived-types)
- [enum](#enums)
- [root](#root)
- [import](#import)
- [wraps](#object-templates)
- [union](#tagged-unions)

Comments are written using the hash (#) character

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
Field declarations themselves are composed of a field name followed by its type
separated by a colon:

```
<field name> : <field type>
```

Field types can be simple types (primitive or derived types), enums, objects
or even arrays of those. For example:

```
object Car {
  model: String,
  brand: String,
  year: Integer
}
```

Objects can be nested. The "Car" object above could be used in a
"CarSale" object declaration, like this:

```
object CarSale {
  description: Car,
  price: Decimal,
  discount: Decimal,
  installments: Integer
}
```

Nesting can also appear as an inline definition. That is, it's not strictly
necessary to register an object beforehand in order to use it in the middle of
another object's definition (if that is the only place that it occurs, for example).
The "Car" example above could very well be defined like the following:

```
object CarSale {
  description: {
    model: String,
    brand: String,
    year: Integer
  },

  price: Decimal,
  discount: Decimal,
  installments: Integer
}
```

By default every field in an object is mandatory. Thus, if any field is not
present in the JSON string being deserialized or in the Python object being
serialized, an error will be flagged. If a field is to be optional, just prefix
the field definition with the **"optional"** directive, like this:

```
object Address {
  street: String,
  number: Integer,
  zipCode: String,
  optional complement: String
}
```

Optional fields, when present, must obey the type and specialization defined for them.
Also, by default, no fields can be assigned null values. To allow specific fields to accept
null values, prefix its type as **nullable**, like this:

```
object order {
  itemId: Integer,
  value: Decimal,
  shipping: nullable Address
}

```

> **_NOTE:_** An optional nullable field is thus the most liberal definition a field can have.
In this case, the field may or may not be present in either the JSON instance (deserialization)
or in the Python object (serialization), and if present, it can also be null.

Objects can be extended, which means you can define a new object type based on an
existing one. It'll inherit all the fields defined in its parent or that the parent itself
inherited. It's not possible, however, to redefine fields using the same field name in
child objects that are already present in any of its ancestors, an error will be raised during
schema parsing if you inadvertently do so. The syntax is as follows:

```
object <child object name> extends <parent object name> {
  <new field declaration>,
  <new field declaration>,
  ...
}
```

For example:

```
object Point2d {
  x: Float,
  y: Float
}

object Point3d extends Point2d {
  z: Float
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
Once defined, a derived type can be used to specify a field's content just like
a primitive type. For example:

```
type Percent : Decimal (min=0.00, max=100.00)
type UnitRange : Float (min=-1, max=+1)
type Normalized : UnitRange (min=0)

object values {
  increase: Percent,
  cosine: Normalized
}
```

When registering a new derived type, it's possible to change previously defined specificities.
This means you can alter some or all the specificities already defined in a base type,
be it during the declaration of a new type as well directly in the field declaration,
like in the following scenario:

```
type BroadScale : Float (min=0, max=999)
type NarrowScale : BroadScale (max=99)

object scaled {
  restrictedScale : NarrowScale (max=9)
}
```


## Enums

Enums can be employed to define types whose values are part of a limited set. They
need to be JavaScript **strings** and will be deserialized into Python's **str** and vice
versa. As one might expect, if an enum field holds a value that is not in the allowed set during
serialization/deserialization, an error will be flagged.
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
object Sale {
  amount: Decimal (min=0.00),
  status: {
    AWAITING,
    PAID,
    REJECTED,
    CANCELLED
  }
}
```

## Root

**root** defines the contents that need to be present in a JSON string for it to be
validated and further deserialized, and conversely, the contents that need to be present
in a Python object for it to be serialized. The **root** directive can receive a simple type,
an enum or an object, either through a named type or an inline definition:

Example 1
```
root Integer
```

Example 2
```
root String (maxLength=128)
```

Example 3
```
root { IDLE, BUSY }
```

Example 4
```
root {
  username: String(minLength=3),
  password: String(minLength=8)
}
```

Example 5
```
object Credentials {
  username: String(minLength=3),
  password: String(minLength=8)
}

root Credentials
```

Only one root can be declared by schema file. Declaring two or more roots
will characterize a schema as ambiguous and jsonbp will complain during
schema parsing.

## Import

Schema files can be imported by other schema files in order to reuse the
definitions present in them. The syntax is:

```
include <path to schema file inside quotes including extension>
```

The search path is relative to the schema file that has the "include" directive.
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

- Inside **schema00.jbp**
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

## Object Templates

Object templates allow you to define a reusable object structure with a single
type parameter. The **wraps** directive declares the parameter name, which can
then be used as a field type anywhere inside the object body:

```
object <template name> wraps <parameter> {
  <field declaration>,
  ...
}
```

For example, a generic pageable wrapper can be defined once and reused with any
content type:

```
object Pageable wraps T {
  contents: T[],
  hasNext: Bool,
  page: Integer,
  total: Integer
}
```

To use a template, provide a concrete type in angle brackets at the use site:

```
object User {
  id: Integer,
  name: String
}

root Pageable<User>
```

This creates a concrete type `Pageable<User>` whose `contents` field holds an
array of `User` objects. The concrete type is stamped out once at parse time and
reused if the same combination appears again.

The type argument can be any named type — an object, an enum, or a primitive type:

```
enum Status { ACTIVE, INACTIVE }

root {
  userPage: Pageable<User>,
  statusPage: Pageable<Status>,
  numberPage: Pageable<Integer>
}
```

Template definitions can be placed in a separate schema file and imported:

```
# pageable.jbp
object Pageable wraps T {
  contents: T[],
  hasNext: Bool,
  total: Integer
}
```

```
# main.jbp
include "pageable.jbp"

object User { id: Integer, name: String }

root Pageable<User>
```

Caveats:
- Only a single type parameter is supported per template.
- Template names share the same namespace as objects, types, and enums — duplicates will raise a schema error.
- A template cannot be used as a root or field type directly; it must always be instantiated with a concrete type argument.


## Tagged Unions

The **union** directive defines a type whose shape depends on the value of a
designated **discriminator** field. This is sometimes called a discriminated
union or a tagged union, and is common in APIs that return payloads of different
shapes depending on a type tag. The syntax is:

```
union <union name> on "<discriminator field>" {
  "<tag value>" => <branch type>,
  "<tag value>" => <branch type>,
  ...
}
```

Each branch maps a quoted tag value to a concrete object type. Branch types can
be either a named object or an inline object definition (including `extends`):

```
object Base {
  from: String,
  id: String,
  timestamp: String
}

object TextMessage extends Base {
  body: String
}

object ReactionMessage extends Base {
  emoji: String,
  message_id: String
}

union Message on "type" {
  "text"     => TextMessage,
  "reaction" => ReactionMessage,
  "image"    => extends Base { url: String, optional caption: String }
}
```

When deserializing, jsonbp reads the discriminator field and dispatches to the
matching branch. The discriminator value is preserved in the resulting Python
dict alongside the branch fields:

```python
success, result = blueprint.deserialize('{"type": "text", "from": "Alice", "id": "1", "timestamp": "t", "body": "hello"}')
# result == {"type": "text", "from": "Alice", "id": "1", "timestamp": "t", "body": "hello"}
```

Unions can be used as field types or as root:

```
root Message

# or inside an object

root {
  event: Message,
  events: Message[]
}
```

The discriminator field name must be quoted as a string because common names
such as `type` are reserved keywords in the DSL.

Caveats:
- Union names share the same namespace as objects, types, and enums — duplicates will raise a schema error.
- A branch must reference a named object or provide an inline object definition; enums and primitive types are not valid branch types.
- Trailing commas are allowed after the last branch.

