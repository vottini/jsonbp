
_lengthInBytes = 4
_lengthInBits = (_lengthInBytes * 8)
_signalizedMaxBits = _lengthInBits - 1
greatestNumber = (1 << _signalizedMaxBits) - 1
lowestNumber = -(1 << _signalizedMaxBits)

__all__ = [
	"greatestNumber",
	"lowestNumber"
]

