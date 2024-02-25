# Instructions to create, to build and to create documentation on a package

## Create virtual environment

python3 -m venv .venv \
source .venv/bin/activate

pip install --upgrade pip
pip install pip-tools

## Install requirements for development

pip-compile ./requirements-dev.in \
pip-sync requirements-dev.txt

## Install requirements for produuction

pip-compile ./requirements.in \
pip-sync requirements.txt

## Upgrade/update requirements

pip-compile --upgrade
pip-compile --upgrade-package 'packagename'
pip-sync

## Create the package repository on PyPi

## Create documentation

mkdocs new . # to create a new documents area \
mkdocs serve # to preview live the documentation \
mkdocs build # to build the site \
mkdocs gh-deploy # to deploy it to *GitHub*

## Build and install on *pypi*

python3 -m build \
twine upload -u pcachim -p pacti6-qafhec-rarQen dist/*
