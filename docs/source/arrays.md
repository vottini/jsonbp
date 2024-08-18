# Arrays

To make any field an array, just add brackets "[]" at the end of its
declaration. The field can be either a simple type, an enum or a node.
During deserialization, jsonbp will check if the value is, in fact, an **Array**,
(even a empty one) and will reject the JSON instance otherwise. If it is
correctly validated by jsonbp, the result will be a Python **list**.
For example:

```
node point2d {
  x: float,
  y: float
}

root {
  points: point2d[],
  deltaTs: float (min=0.0) [minLength=2],
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

root point2d[]
```

Inside the brackets, arrays can have three "specificities" defined. As ilustrated by the above
examples, two of them are **minLength** and **maxLength** that respectively limits the
minimum and maximum number of elements the array may contain. **maxLength** must
be equal or greater than **minLength**, or an exception will be raised during parsing.

The third one is **nullableArray** which, as name implies, allows an array field to be
null. This is necessary to differentiate an array with possibly nullable items from
an array field that it itself can be null. For example, given the following schema:

```
root {
  case_a: double[],
  case_b: nullable double[],
  case_c: nullable double[nullableArray=true]
}
```

The field **case_a** is not allowed to be null and should contain strictly non-null
values. Similiarly, **case_b** must too be a non-null array, however it might contain
null values. On the other hand, **case_c** can be potentially null, and if not null, it
also can bear null values.

