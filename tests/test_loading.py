
import os
import pytest
import sys

sys.path.append('..')
import jsonbp

modulesDir = 'modules'

def testLoading():
	blueprint = jsonbp.loadFile(
		os.path.join(modulesDir, 'blueprint.jbp'),
		[os.path.join(modulesDir, 'valid')])

	jsonbp.invalidateCache()
	with pytest.raises(jsonbp.SchemaViolation):
		blueprint = jsonbp.loadFile(
			os.path.join(modulesDir, 'blueprint.jbp'),
			[os.path.join(modulesDir, 'invalid')])


if __name__ == "__main__":
	testLoading()

