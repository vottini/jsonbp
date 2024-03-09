
import sys
sys.path.append('..')
import jsonbp

def testLocaleEdges():
	jsonbp.loadTranslation("inexistentFile", "it_IT")
	blueprint = jsonbp.loadString('''root { positions: integer(min=0) [maxLength=128] }''')
	badInstance = ''' {"positions": [ 32, 12, "Wally"]}'''

	success, outcome = blueprint.deserialize(badInstance)
	print(outcome.format(["it_IT", "pt_BR", "en_US"]))
	jsonbp.useDefaultLanguage('nonExistent')
	print(str(outcome))


if __name__ == "__main__":
	testLocaleEdges()

