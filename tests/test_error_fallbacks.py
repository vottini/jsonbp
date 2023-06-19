
import sys
sys.path.append('..')
import jsonbp

def testLocaleEdges():
	jsonbp.useLanguage('nonExistent')
	jsonbp.useLanguage('missing')
	blueprint = jsonbp.loadString('''root { positions: integer(min=0) [maxLength=128] }''')
	# tests blueprint's str()
	print(blueprint)

	badInstance = ''' {"positions": [ 32, 12, "Wally"]}'''
	success, outcome = blueprint.deserialize(badInstance)
	#should print half english (missing part) and half portuguese
	print(str(outcome))


if __name__ == "__main__":
	testLocaleEdges()

