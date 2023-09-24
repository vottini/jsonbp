
import os
import os.path
import sys

from decimal import Decimal
from datetime import datetime, timedelta, timezone
import pytest

verificationDir = 'serialization'
verificationSubdirs = [f.name
	for f in os.scandir(verificationDir)
	if f.is_dir()]

trialColumns = (
	'description',
	'file',
	'expectedOutcome'
)

verifications = dict()
verificationSubdirs.sort()
verificationsTotal = 0

for subdir in verificationSubdirs:
	subdirPath = os.path.join(verificationDir, subdir)
	blueprintFile = os.path.join(subdirPath, 'blueprint.jbp')
	trialFile = os.path.join(subdirPath, 'trials.txt')

	for necessaryFile in (blueprintFile, trialFile):
		if not os.path.isfile(necessaryFile):
			print(f"[WARN] In subdir '{subdir}': either blueprint or trial files are absent, skipping...")
			break

	else:
		trials = list()
		lineNo = 0

		with open(trialFile) as fd:
			for line in fd:
				lineNo += 1

				sanedLine = line.strip()
				if len(sanedLine) == 0 or sanedLine[0] == '#':
					continue

				columns = sanedLine.split('|')
				if len(columns) != len(trialColumns):
					print(f"[WARN] In file '{trialFile}' at line {lineNo}: fewer columns than necessary, skipping...")
					continue

				for i, column in enumerate(columns):
					sanedColum = column.strip()
					if len(column) > 0:
						columns[i] = sanedColum
						continue

					columnName = trialColumns[i]
					print(f"[WARN] In file '{trialFile}' at line {lineNo}: column '{columnName}' is empty, skipping...")
					break
				
				else:
					fullPath = os.path.join(subdirPath, 'data', columns[1])
					if os.path.isfile(fullPath):
						columns[1] = fullPath
						trials.append(columns)

					else:
						print(f"[WARN] In file '{trialFile}' at line {lineNo}: file '{columns[1]}' doesn't exist, skipping...")

		verifications[subdir] = (blueprintFile, trials)
		verificationsTotal += len(trials)

import sys
sys.path.append('..')
import jsonbp

def testSerializations():
	verified = 1

	for key, value in verifications.items():
		blueprintFile, trials = value
		blueprint = jsonbp.loadFile(blueprintFile)
		data = {}

		for trial in trials:
			description, dataFile, expectedOutcome = trial
			print(f'({str(verified).zfill(3)}/{verificationsTotal}) {description} ... ', end='')
			shouldSucceed = "OK" == expectedOutcome

			with open(dataFile) as rfd:
				contents = rfd.read()
				exec(contents)

				inputInData = 'input' in data

				if not inputInData:
					print('Failed!')
					print(f'In file "{dataFile}": "input" was not defined for dict data')
					print('It was not possible to check serialization')

				if expectedOutcome == "OK":
					serialized = blueprint.serialize(data['input'])
					success, outcome = blueprint.deserialize(serialized)
					assert success and outcome == data['input']

				else:
					with pytest.raises(jsonbp.SerializationException):
						serialized = blueprint.serialize(data['input'])

			print("OK")
			verified += 1

if __name__ == "__main__":
	testSerializations()

