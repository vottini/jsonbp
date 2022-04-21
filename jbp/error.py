
class error:

	INTEGER_PARSING = 0	 # text
	FLOAT_PARSING   = 1	 # text
	FIXED_PARSING   = 2	 # text
	OUTSIDE_RANGE   = 3	 # field, value
	INVALID_BOOLEAN = 4	 # value
	INVALID_STRING  = 5	 # field, value
	INVALID_LENGTH  = 6	 # field, length

	texts = {
		INTEGER_PARSING: 'Unable to parse "{text}" as integer',
		FLOAT_PARSING: 'Unable to parse "{text}" as float',
		FIXED_PARSING: 'Unable to parse "{text}" as fixed',
		OUTSIDE_RANGE: 'Field "{field}": value {value} is outside expected range',
		INVALID_BOOLEAN: 'Value must be "true" or "false", got "{value"}',
		INVALID_STRING: 'Field "{field}": invalid string value received',
		INVALID_LENGTH: 'Field "{field}": length {length} is out of expected range'
	}

	def __init__(self, error_id, **context):
		self.error_id = error_id
		self.context = context

	def __str__(self):
		msg = error.texts[self.error_id]
		return msg.format(**self.context)

	def getErrorType(self):
		return self.error_id

