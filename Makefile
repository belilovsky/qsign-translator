.PHONY: install install-api check api bootstrap-local benchmark smoke-live

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

benchmark:
	PYTHONPATH=src python3 scripts/benchmark_planner.py

smoke-live:
	python3 scripts/smoke_live.py --base-url $${BASE_URL:-https://qsign.qdev.run} $${REVIEW_TOKEN:+--review-token "$$REVIEW_TOKEN"}
