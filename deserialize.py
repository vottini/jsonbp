
import sys
import jsonbp

if len(sys.argv) < 3:
	print(f"Usage: {sys.argv[0]} <blueprint> <json>")
	sys.exit(0)

blueprintFile = sys.argv[1]
blueprint = jsonbp.loadFile(blueprintFile)
print(blueprint)

jsonFile = sys.argv[2]
with open(jsonFile, "r") as fd:
	success, result = blueprint.deserialize(fd.read())
	print(f'Success: {success}')
	print(f'Result: {result}')

	if success:
		original = blueprint.serialize(result)
		print(f'Original: {original}')

