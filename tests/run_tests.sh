#!/bin/bash

coverage run -m pytest -v && coverage report --omit="*/jsonbp/ply/*,test_*.py" --show-missing
