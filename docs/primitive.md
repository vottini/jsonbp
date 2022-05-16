
* Primitive types

These are the primitive types that jsonbp accepts and the corresponding Python types that they map to:

integer => int
float => float
fixed => Decimal
bool => bool
datetime => datetime
string => str

When used in a field definition, they can be customized through specificities, which is a list of pair-values enclosed in parenthesis and separated by commas. Each type has a fixed and well defined list os possible specificities.
