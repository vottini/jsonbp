
class error:

	ERR_INTEGER_PARSING = 0	 # text
	ERR_FLOAT_PARSING   = 1	 # text
	ERR_FIXED_PARSING   = 2	 # text
	ERR_OUTSIDE_RANGE   = 3	 # field, value

	texts = {
		ERR_INTEGER_PARSING: 'Unable to parse "{text}" as integer',
		ERR_FLOAT_PARSING: 'Unable to parse "{text}" as float',
		ERR_FIXED_PARSING: 'Unable to parse "{text}" as fixed',
		ERR_OUTSIDE_RANGE: 'Field "{field}": value {value} is outside expected range'
	}

	def __init__(self, error_id, **context):
		self.error_id = error_id
		self.context = context

	def __str__(self):
		msg = error.texts[self.error_id]
		return msg.format(**self.context)

