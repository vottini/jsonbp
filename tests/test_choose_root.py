
import pytest

blueprint_txt = """

	enum Origin {
		ACQUIRED,
		RECEIVED,
		GUESSED
	}

	object Position {
		latitude: Float (atLeast=-90, atMost=+90),
		longitude: Float (atLeast=-180, atMost=+180)
	}

	object Payload {
		position: Position,
		origin: Origin
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
	blueprint = jsonbp.load_string(blueprint_txt)

	bad_calls = [
		(lambda : blueprint.deserialize(json_txt), jsonbp.SchemaViolation),
		(lambda : blueprint.choose_root("nonExistent"), jsonbp.SchemaViolation),
		(lambda : blueprint.serialize({"foo": "bar"}), jsonbp.SerializationException)
	]

	for bad_call, excepionType in bad_calls:
		with pytest.raises(excepionType):
			bad_call()

	derived = blueprint.choose_root("Payload")
	success, _ = derived.deserialize(json_txt)
	assert success

	arrayDerived = blueprint.choose_root("Payload", as_array=True,
		min_array_length=2, max_array_length=3)

	outcome1, _ = arrayDerived.deserialize(f"[{json_txt}, {json_txt}]")
	outcome2, _ = arrayDerived.deserialize(f"[{json_txt}, {json_txt}, {json_txt}, {json_txt}]")
	assert outcome1 == True and outcome2 == False

if __name__ == "__main__":
	testChooseRoot()

