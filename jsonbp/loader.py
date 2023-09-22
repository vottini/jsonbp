
import os
import sys
import uuid
import importlib.util

_required_fields = [
	"name",
	"parser",
	"formatter",
	"defaults"
]

def listScripts(path):
	try: path_files = os.listdir(path)
	except FileNotFoundError:
		return list()

	return [
		os.path.join(path, f) for f in path_files
			if os.path.isfile(os.path.join(path, f))
			and f.endswith(".py")
	]


def loadTypes(path):
	files = listScripts(path)
	if not path in sys.path:
		sys.path.insert(0, path)

	loaded = list()
	notLoaded = list()
	for file_path in files:
		random_name = str(uuid.uuid1())

		try:
			spec = importlib.util.spec_from_file_location(random_name, file_path)
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)

			if hasattr(module, 'type_specs'):
				for field in _required_fields:
					if not field in module.type_specs:
						msg = "Missing required field '{field}'"
						notLoaded.append((file_path, msg))
						continue

				loaded.append(module.type_specs)

		except Exception as e:
			notLoaded.append((file_path, e))
			continue

	return loaded, notLoaded

