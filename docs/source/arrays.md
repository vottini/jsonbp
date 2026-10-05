# Arrays

To make any field an array, just add brackets "[]" at the end of its
declaration. The field can be a simple type, an enum or an object.
During deserialization, jsonbp will check if the value is, in fact, an **Array**,
(even an empty one) and will reject the JSON instance otherwise. If the field is
correctly validated by jsonbp, the result will be a Python **list**.
For example:

```
object Point2d {
  x: Float,
  y: Float
}

root {
  points: Point2d[],
  deltaTs: Float (min=0.0) [minLength=2],
  conditions: {
    GOOD,
    REGULAR,
    BAD,
    REJECTED
  } [minLength=1, maxLength=3]
}
```

**root** itself can also be an array:

```
root {
  APPLE,
  ORANGE,
  STRAWBERRY,
  PINEAPLE
} [minLength=2, maxLength=2]

# or even

root Point2d[]
```

Inside the brackets, arrays can have three "specificities" defined. As illustrated by the
examples above, two of these are **minLength** and **maxLength** that respectively limit the
minimum and maximum number of elements the array may contain. **maxLength** must
be equal to or greater than **minLength**, or an exception will be raised during parsing.

The third is **nullableArray** which, as the name implies, allows an array field to be
null. This is necessary to differentiate an array with possibly nullable items from
an array field that itself can be null. For example, given the following schema:

```
root {
  case_a: Float[],
  case_b: nullable Float[],
  case_c: nullable Float[nullableArray=true]
}
```

The field **case_a** is not allowed to be null and should contain strictly non-null
values. Similarly, **case_b** must also be a non-null array, however it might contain
null values. On the other hand, **case_c** can be potentially null, and if it's not null, it
can also contain null values.

