
import sys
import jsonbp

if len(sys.argv) < 3:
	print(f"Usage: {sys.argv[0]} <blueprint> <json>")
	sys.exit(0)

blueprintFile = sys.argv[1]
prober = jsonbp.load(blueprintFile)
#print(prober)

jsonFile = sys.argv[2]
with open(jsonFile, "r") as fd:
	success, payload = prober.deserialize(fd.read())
	print(f'{success} -> {payload}')

