
print("Running deserialization tests...")

import os
import os.path
import sys

from decimal import Decimal
from datetime import datetime

verificationDir = 'tests/deserialization'
verificationSubdirs = [f.name
	for f in os.scandir(verificationDir)
	if f.is_dir()]

trialColumns = (
	'description',
	'file',
	'expectedOutcome',
	'expectedResult'
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
					fullPath = os.path.join(subdirPath, 'instances', columns[1])
					if os.path.isfile(fullPath):
						columns[1] = fullPath
						trials.append(columns)

					else:
						print(f"[WARN] In file '{trialFile}' at line {lineNo}: file '{columns[1]}' doesn't exist, skipping...")

		verifications[subdir] = (blueprintFile, trials)
		verificationsTotal += len(trials)

import sys
import jsonbp
import jbp.error as jbpError

def abort(filename):
	print(f"Aborting on file: {filename}")
	sys.exit(0)

verified = 1
for key, value in verifications.items():
	blueprintFile, trials = value
	blueprint = jsonbp.load(blueprintFile)

	for trial in trials:
		description, jsonFile, expectedOutcome, expectedResult = trial
		print(f'({verified}/{verificationsTotal}) {description} ... ', end='')
		shouldSucceed = "OK" == expectedOutcome

		with open(jsonFile, "r") as fd:
			outcome, obtainedResult = blueprint.deserialize(fd.read())
			correct = (outcome == shouldSucceed)

			if not correct:
				print('Failed!')
				print(f'Expected outcome = {shouldSucceed}')
				print(f'Obtained outcome = {outcome}')
				print("###", obtainedResult)
				abort(blueprintFile)

			if not shouldSucceed:
				expectedError = getattr(jbpError, expectedResult)
				returnedError = obtainedResult.getErrorType()
				print(f'[{obtainedResult}] ', end='')

				if expectedError != returnedError:
					print('Failed!')
					print('Expected error differs from obtained error:')
					print(f'Expected error id = {expectedError}')
					print(f'Obtained error id = {returnedError}')
					abort(blueprintFile)

			else:
				subdirPath = os.path.join(verificationDir, key)
				resultFile = os.path.join(subdirPath, 'benchmarks', expectedResult)

				if not os.path.isfile(resultFile):
					print('Failed!')
					print(f'Unable to open file "{resultFile}"')
					print('It was not possible to check deserialization')
					abort(blueprintFile)

				else:
					with open(resultFile) as rfd:
						contents = rfd.read()
						exec(contents)

						if not 'result' in locals():
							print('Failed!')
							print(f'In file "{resultFile}": "result" is not defined')
							print('It was not possible to check deserialization')
							abort(blueprintFile)

						if not obtainedResult == result:
							print('Failed!')
							print(f'Obtained result = {obtainedResult}')
							print(f'Expected result = {result}')
							abort(blueprintFile)

						del result

			print('OK')

		verified += 1
