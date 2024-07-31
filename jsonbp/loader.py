
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

def list_scripts(path):
	try: path_files = os.listdir(path)
	except FileNotFoundError:
		return list()

	return [
		os.path.join(path, f) for f in path_files
			if os.path.isfile(os.path.join(path, f))
			and f.endswith(".py")
	]


def load_types(path):
	files = list_scripts(path)
	if not path in sys.path:
		sys.path.insert(0, path)

	loaded = list()
	not_loaded = list()
	for file_path in files:
		random_name = str(uuid.uuid1())

		try:
			spec = importlib.util.spec_from_file_location(random_name, file_path)
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)

			if hasattr(module, 'type_specs'):
				for field in _required_fields:
					if not field in module.type_specs:
						msg = f"Missing required field '{field}'"
						not_loaded.append((file_path, msg))
						continue

				loaded.append(module.type_specs)

		except Exception as e:
			not_loaded.append((file_path, e))
			continue

	return loaded, not_loaded

