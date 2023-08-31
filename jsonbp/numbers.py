
_bytesLength = 4
_maxBits = (_bytesLength * 8)
_signalizedMaxBits = _maxBits - 1

greatest = (1 << _signalizedMaxBits) - 1
lowest = -(1 << _signalizedMaxBits)

__all__ = [
	"greatest",
	"lowest"
]

