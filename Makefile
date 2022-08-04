# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io

PYTHON=python3
PYTHON_SOURCES=$(shell git ls-files "*.py")

.PHONY: pylint
pylint:
	$(PYTHON) -m pylint --exit-zero --rcfile .pylintrc $(PYTHON_SOURCES)

.PHONY: flake8
flake8:
	$(PYTHON) -m flake8 --exit-zero --config .flake8 $(PYTHON_SOURCES)

