#!/bin/bash

mkdir -p package/src
rm -rf package/dist
cp -r jsonbp package/src/

cd package
python3.9 setup.py sdist
CREATED_PACKAGE=$(ls dist/)
rm -r src

echo ""
echo "* Package '${CREATED_PACKAGE}' created"
echo "* Upload it to PyPI with command:"
echo "$ twine upload package/dist/${CREATED_PACKAGE} --repository jsonbp"
