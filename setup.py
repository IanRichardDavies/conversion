# Package Imports
from setuptools import find_packages, setup

setup(
	name="conversion",
	author="Ian Davies",
	author_email="ird.davies@gmail.com",
	license="MIT",
	include_package_data=True,
	packages=find_packages(),
	tests_require=["pytest"],
)