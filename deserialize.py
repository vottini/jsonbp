
import sys
import jsonbp

if len(sys.argv) < 3:
	print(f"Usage: {sys.argv[0]} <blueprint> <json> [additional type dirs]*")
	sys.exit(0)

typeDirs = None
if len(sys.argv) > 3:
	typeDirs = sys.argv[3:]

blueprintFile = sys.argv[1]
blueprint = jsonbp.loadFile(blueprintFile, typeDirs)
print(blueprint)

jsonFile = sys.argv[2]
with open(jsonFile, "r") as fd:
	success, result = blueprint.deserialize(fd.read())
	print(f'Success: {success}')
	print(f'Result: {result}')

	if success:
		original = blueprint.serialize(result)
		print(f'Original: {original}')

