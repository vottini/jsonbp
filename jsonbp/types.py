
class ErrorType:
	JSON_PARSING     = 0   # line, column, message
	VALUE_PARSING    = 1   # type
	NULL_VALUE       = 2   # field
	OUTSIDE_RANGE    = 3   # value
	INVALID_LENGTH   = 4   # length
	UNKNOWN_LITERAL  = 5   #
	INVALID_ENUM     = 6   #
	INVALID_FORMAT   = 7   #
	MISSING_FIELD    = 8   # field
	INVALID_ARRAY    = 9   #
	INVALID_OBJECT   = 10  #


class FieldType:
	SIMPLE = 0
	ENUM   = 1
	OBJECT = 2


class unquoted_str(str):
	pass

