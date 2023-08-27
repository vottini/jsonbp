
class WrappedNumber:
	def __init__(self, strValue): self.strValue = strValue
	def __str__(self): return self.strValue
	__repr__ =  __str__


class WrappedConstant:
	def __init__(self, strValue): self.strValue = strValue
	def __str__(self): return self.strValue
	__repr__ =  __str__

