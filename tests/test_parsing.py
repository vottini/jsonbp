
import os
import os.path
import pytest

verificationDir = 'parsing'
verificationSubdirs = [f.name
	for f in os.scandir(verificationDir)
	if f.is_dir()]

verifications = dict()
verificationSubdirs.sort()
verificationsTotal = 0

for subdir in verificationSubdirs:
	subdirPath = os.path.join(verificationDir, subdir)
	blueprintFile = os.path.join(subdirPath, 'blueprint.jbp')

	if not os.path.isfile(blueprintFile):
		print(f"[WARN] In subdir '{subdir}': blueprint is absent, skipping...")
		break

	else:
		verifications[subdir] = blueprintFile
		verificationsTotal += 1

import sys
sys.path.append('..')
import jsonbp

def testViolations():
	verified = 1
	for subdir, blueprintFile in verifications.items():
		print(f'({str(verified).zfill(2)}/{verificationsTotal}) {subdir} ... ', end='')

		with pytest.raises(jsonbp.SchemaViolation):

			try:
				blueprint = jsonbp.load(blueprintFile)
				print("KO => Error not found")
				print("Aborting...")
				break
			
			except jsonbp.SchemaViolation as e:
				print(f"OK <{e}>")
				verified += 1
				raise e


if __name__ == "__main__":
	testViolations()
