
import sys
sys.path.append('..')
import jsonbp

def testCaching():
	blueprintFile = 'login.jbp'
	blueprint1 = jsonbp.load_file(blueprintFile)
	blueprint2 = jsonbp.load_file(blueprintFile)
	assert blueprint1 == blueprint2

	jsonbp.invalidate_cache()
	blueprint3 = jsonbp.load_file(blueprintFile)
	assert blueprint3 != blueprint1

if __name__ == "__main__":
	testCaching()

