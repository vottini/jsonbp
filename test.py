
import sys
import jsonbp

if len(sys.argv) < 3:
	print(f"Usage: {sys.argv[0]} <blueprint> <json>")
	sys.exit(0)

blueprintFile = sys.argv[1]
jsonFile = sys.argv[2]

prober = jsonbp.load(blueprintFile); print(prober)

with open(jsonFile, "r") as fd:
	jsContents = fd.read()
	success, payload = prober.deserialize(jsContents)
	print(f'{success} -> {payload}')

