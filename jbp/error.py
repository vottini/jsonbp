
class error:

	INTEGER_PARSING = 0	 # field, text
	FLOAT_PARSING   = 1	 # field, text
	FIXED_PARSING   = 2	 # field, text
	OUTSIDE_RANGE   = 3	 # field, value
	INVALID_BOOLEAN = 4	 # field, value
	INVALID_STRING  = 5	 # field, value
	INVALID_LENGTH  = 6	 # field, length
	NULL_VALUE		  = 7	 # field

	texts = {
		INTEGER_PARSING: 'Field "{field}": unable to parse "{text}" as integer',
		FLOAT_PARSING: 'Field "{field}": unable to parse "{text}" as float',
		FIXED_PARSING: 'Field "{field}": unable to parse "{text}" as fixed',
		OUTSIDE_RANGE: 'Field "{field}": value {value} is outside expected range',
		INVALID_BOOLEAN: 'Field "{field}": value must be "true" or "false", got "{value}"',
		INVALID_STRING: 'Field "{field}": Not a valid string',
		INVALID_LENGTH: 'Field "{field}": length {length} is out of expected range',
		NULL_VALUE: 'Field "{field}" has null value'
	}

	def __init__(self, error_id, field,  **context):
		self.error_id = error_id
		self.context = context
		self.field = field

	def __str__(self):
		msg = error.texts[self.error_id]
		return msg.format(field=self.field, **self.context)

	def getErrorType(self):
		return self.error_id

