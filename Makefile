# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io

PYTHON=python3
PYTHON_SOURCES=$(shell git ls-files "*.py")

.PHONY: pylint
pylint:
	$(PYTHON) -m pylint --rcfile .pylintrc $(PYTHON_SOURCES) --ignored-modules=psycopg2.errors

.PHONY: flake8
flake8:
	$(PYTHON) -m flake8  --config .flake8 $(PYTHON_SOURCES)

