
import sys
import jsonbp

if len(sys.argv) < 3:
	print(f"Usage: {sys.argv[0]} <blueprint> <json>")
	sys.exit(0)

blueprintFile = sys.argv[1]
blueprint = jsonbp.load(blueprintFile)
print(blueprint, "\n")

jsonFile = sys.argv[2]
with open(jsonFile, "r") as fd:
	success, result = blueprint.deserialize(fd.read())
	print(f'!!! {success} -> {result}')

