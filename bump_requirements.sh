#!/bin/bash

git checkout dev
# conda update --all -y
# nosetests pgmpy/tests/ -q

versions = $(pip freeze)

if [ $? -eq 0 ]
then
	echo "Tests Success"
	for line in requirements.txt;
	do
		package = $line
		new_version = $(pip freeze | grep $package)
	done
else
	echo "Tests Failed"
	exit 1
fi
