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
  deltaTs: double (min=0.0) [minLength=2],
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

Arrays can have three "specificities". As ilustrated by the above examples,
two of them are **minLength** and **maxLength** that respectively limits the
minimum and maximum number of elements the array may contain. **maxLength** must
be equal or greater than **minLength**, or an exception will be raised during parsing.

The third one is **nullableArray**, which as name implies, allows an array field to be
null. This is necessary to differentiate an array with possibly nullable items from
an array field that itself can be null.
