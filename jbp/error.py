
JSON_PARSING	   = 14	 # line, column, message
NULL_VALUE		   = 7	 # 
INTEGER_PARSING  = 0	 # text
FLOAT_PARSING    = 1	 # text
FIXED_PARSING    = 2	 # text
OUTSIDE_RANGE    = 3	 # value
INVALID_BOOLEAN  = 4	 # value
INVALID_STRING   = 5	 # value
INVALID_LENGTH   = 6	 # length
INVALID_DATETIME = 8	 # text
UNKNOWN_LITERAL  = 9	 # text
INVALID_ENUM     = 10	 # value
MISSING_FIELD    = 11  # field
INVALID_ARRAY    = 12  # 
INVALID_NODE     = 13  # 

texts = {
	JSON_PARSING: 'Invalid JSON, error at line {line}, column {column}: {message}',
	NULL_VALUE: 'Null value',
	INTEGER_PARSING: 'Unable to parse "{text}" as integer',
	FLOAT_PARSING: 'Unable to parse "{text}" as float',
	FIXED_PARSING: 'Unable to parse "{text}" as fixed',
	OUTSIDE_RANGE: 'Value {value} is outside expected range',
	INVALID_BOOLEAN: 'Value must be "true" or "false", got "{value}"',
	INVALID_STRING: 'Not a valid string',
	INVALID_LENGTH: 'Length {length} is out of expected range',
	INVALID_DATETIME: '"{text}" doesn\'t match expected datetime format',
	UNKNOWN_LITERAL: 'Unknown value "{value}"',
	INVALID_ENUM: 'Not a valid string',
	MISSING_FIELD: 'Missing field "{field}"',
	INVALID_ARRAY: 'Needs to be an array',
	INVALID_NODE: 'Needs to be a dictionary'
}

prefixes = {
	"FIELD": 'Field "{assignee}":',
	"NODE": 'Node "{assignee}":',
	"ARRAY": 'In array "{assignee}" at index {index}:',
	"ROOT": 'At root level:'
}

class instance:
	def __init__(self, error_id, **context):
		self.error_id = error_id
		self.context = context
		self.prefix = None
		self.assignee = None
		self.index = None

	def getErrorType(self):
		return self.error_id

	def setAssignee(self, assigneeType, assigneeName=None):
		self.prefix = assigneeType
		self.assignee = assigneeName

	def setAsArrayElement(self, arrayIndex):
		self.prefix = "ARRAY"
		self.index = arrayIndex

	def __str__(self):
		prefixText = ""
		if None != self.prefix:
			prefix = prefixes[self.prefix]
			prefixText = prefix.format(
				assignee=self.assignee,
				index=self.index)

		msg = texts[self.error_id]
		errorMsg = msg.format(**self.context)
		return " ".join([prefixText, errorMsg])

#-------------------------------------------------------------------------------

def createForField(fieldName, error_id, **context):
	result = instance(error_id, **context)
	args = ("FIELD", fieldName) if fieldName != None else ("ROOT",)
	result.setAssignee(*args)
	return result


def createForNode(nodeName, error_id, **context):
	result = instance(error_id, **context)
	args = ("NODE", nodeName) if nodeName != None else ("ROOT",)
	result.setAssignee(*args)
	return result


def createForRoot(error_id, **context):
	result = instance(error_id, **context)
	result.setAssignee("ROOT")
	return result

