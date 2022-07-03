
from setuptools import setup, find_packages

with open("README.rst", "r") as fd:
	long_description = fd.read()

setup(
	name='jsonbp',
	description='JSON Python Deserializer',
	version='0.9.1',
	license='MIT',
	python_requires='>=3.6',
	platforms='any',
	author="Gustavo Venturini",
	author_email='gustavo.c.venturini@gmail.com',
	packages=find_packages('src'),
	package_dir={'': 'src'},
	include_package_data=True,
	url='https://github.com/vottini/jsonbp',
	keywords=['json', 'deserialization'],
	long_description=long_description,
	long_description_content_type="text/markdown",
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Programming Language :: Python :: 3 :: Only",
	],
)
