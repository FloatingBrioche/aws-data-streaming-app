# Makefile to build the project

## Environment variables
PROJECT_NAME=aws-data-streaming-app
PYTHON_INTERPRETER=python
WD=$(shell pwd)
PYTHONPATH=${WD}
SHELL:=/bin/bash
PIP:=pip
REGION = eu-west-2

### Set up environment ###

## Create python interpreter environment
create-environment:
	@echo ">>> Project: $(PROJECT_NAME)..."
	@echo ">>> Python version:"
	( \
		$(PYTHON_INTERPRETER) --version; \
	)
	@echo ">>> Setting up VirtualEnv"
	( \
	    $(PIP) install -q virtualenv virtualenvwrapper; \
	    virtualenv venv --python=$(PYTHON_INTERPRETER); \
	)

## Define utility variable to help calling Python from the virtual environment
ACTIVATE_ENV:=source venv/bin/activate

## Execute python related functionalities from within the project's environment
define execute_in_env
	$(ACTIVATE_ENV) && export PYTHONPATH=${PYTHONPATH} && $1
endef

## Execute Terraform related functionalities within the terraform directory
define execute_in_tf
	cd terraform && $1
endef

## Build the dev environment requirements
requirements: create-environment
	$(call execute_in_env, $(PIP) install -r ./dev_requirements.txt)


## Terraform code linting and validation
tf-check:
		$(call execute_in_tf, terraform fmt && terraform validate)


### Run Python Checks ###

## Run bandit security test
security-test:
	$(call execute_in_env, bandit -lll */*.py *c/*/*.py > docs/security_check.txt)

## Run the code check
run-black:
	$(call execute_in_env, black  ./lambda_app/*.py ./test/*/*.py)

## Run the unit tests
unit-test:
	$(call execute_in_env, pytest test/* -vv --testdox)

## Run the coverage check and update coverage documentation
get-coverage:
	$(call execute_in_env, coverage run --source=lambda_app -m pytest  && coverage report -m > ./docs/coverage.txt && coverage-badge -o ./docs/coverage.svg -f)

## Run all checks
run-checks: run-black unit-test get-coverage security-test
