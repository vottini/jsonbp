
import os
import pytest
import sys

sys.path.append('..')
import jsonbp

modulesDir = 'modules'

def testLoading():
	blueprint = jsonbp.load_file(
		os.path.join(modulesDir, 'blueprint.jbp'),
			custom_types=[
				os.path.join(modulesDir, 'valid'),
				os.path.join(modulesDir, 'nonExistent')
			]
		)

	jsonbp.invalidate_cache()

	for directory in ('invalid', 'incomplete'):
		with pytest.raises(jsonbp.SchemaViolation):
			blueprint = jsonbp.load_file(
				os.path.join(modulesDir, 'blueprint.jbp'),
				custom_types=[os.path.join(modulesDir, directory)])


if __name__ == "__main__":
	testLoading()

