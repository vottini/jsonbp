
import sys
sys.path.append('..')
import jsonbp

def testCaching():
	blueprintFile = 'login.jbp'
	blueprint1 = jsonbp.loadFile(blueprintFile)
	blueprint2 = jsonbp.loadFile(blueprintFile)
	assert blueprint1 == blueprint2
	
	jsonbp.invalidateCache()
	blueprint3 = jsonbp.loadFile(blueprintFile)
	assert blueprint3 != blueprint1

if __name__ == "__main__":
	testCaching()

