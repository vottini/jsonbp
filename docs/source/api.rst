
API Reference
=============================

Schema Loading
+++++++++++++++++++++++++++++

.. autofunction:: jsonbp.load_file
.. autofunction:: jsonbp.load_string
.. autofunction:: jsonbp.invalidate_cache


Deserialization/Serialization
+++++++++++++++++++++++++++++

.. autoclass:: jsonbp.JsonBlueprint
  :members: deserialize, serialize, choose_root

.. autoclass:: jsonbp.DeserializationError
  :members: localize

Localization Setup
+++++++++++++++++++++++++++++

.. autofunction:: jsonbp.load_translation
.. autofunction:: jsonbp.use_default_language

Exceptions
+++++++++++++++++++++++++++++

.. autoclass:: jsonbp.SchemaViolation
.. autoclass:: jsonbp.SerializationException

