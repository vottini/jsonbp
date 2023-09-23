
import pytest

blueprint_txt = """

	enum origin {
		ACQUIRED,
		RECEIVED,
		GUESSED
	}

	node position {
		latitude: float (atLeast=-90, atMost=+90),
		longitude: float (atLeast=-180, atMost=+180)
	}

	node payload {
		position: position,
		origin: origin
	}

"""

json_txt = """

{
	"position": {
		"latitude": -22,
		"longitude": -40
	},

	"origin": "ACQUIRED"
}

"""

import sys
sys.path.append('..')
import jsonbp

def testChooseRoot():
	blueprint = jsonbp.loadString(blueprint_txt)
	with pytest.raises(jsonbp.SchemaViolation):
		blueprint.deserialize(json_txt)

	with pytest.raises(jsonbp.SchemaViolation):
		blueprint.chooseRoot("nonExistent")

	derived = blueprint.chooseRoot("payload")
	success, _ = derived.deserialize(json_txt)
	assert success

	arrayDerived = blueprint.chooseRoot("payload", asArray=True,
		minArrayLength=2, maxArrayLength=3)

	outcome1, _ = arrayDerived.deserialize(f"[{json_txt}, {json_txt}]")
	outcome2, _ = arrayDerived.deserialize(f"[{json_txt}, {json_txt}, {json_txt}, {json_txt}]")
	assert outcome1 == True and outcome2 == False

if __name__ == "__main__":
	testChooseRoot()

