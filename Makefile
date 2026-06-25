.PHONY: install install-api check api bootstrap-local

install:
	python3 -m pip install -e ".[test]"

install-api:
	python3 -m pip install -e ".[api,db,test]"

check:
	./scripts/check.sh

api:
	uvicorn qsign_translator.api:app --reload

bootstrap-local:
	./scripts/bootstrap_local.sh
