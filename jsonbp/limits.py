
bytesLength = 4
maxBits = (bytesLength * 8)
signalizedMaxBits = maxBits - 1
greatestNumber = (1 << signalizedMaxBits) - 1
lowestNumber = -(1 << signalizedMaxBits)

