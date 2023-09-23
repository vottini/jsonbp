
import os
import pytest
import sys

sys.path.append('..')
import jsonbp

modulesDir = 'modules'

def testLoading():
	blueprint = jsonbp.loadFile(
		os.path.join(modulesDir, 'blueprint.jbp'), [
			os.path.join(modulesDir, 'valid'),
			os.path.join(modulesDir, 'nonExistent')
		])

	jsonbp.invalidateCache()

	for directory in ('invalid', 'incomplete'):
		with pytest.raises(jsonbp.SchemaViolation):
			blueprint = jsonbp.loadFile(
				os.path.join(modulesDir, 'blueprint.jbp'),
				[os.path.join(modulesDir, directory)])


if __name__ == "__main__":
	testLoading()

