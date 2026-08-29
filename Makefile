PYTHON ?= python3.12

.PHONY: install install-api check check-platform api bootstrap-local benchmark smoke-live

install:
	$(PYTHON) -m pip install -e ".[test]"

install-api:
	$(PYTHON) -m pip install -e ".[api,db,test]"

check:
	QSIGN_PYTHON="$(PYTHON)" ./scripts/check.sh
	$(PYTHON) scripts/check_typography.py
	PYTHONPATH=src $(PYTHON) -m unittest tests.test_typography_policy

check-platform:
	PYTHONPATH=src $(PYTHON) scripts/check_platform_contracts.py --platform-root "$${PLATFORM_ROOT:?set PLATFORM_ROOT to the Platform Portal checkout}"

api:
	uvicorn qsign_translator.api:app --reload

bootstrap-local:
	./scripts/bootstrap_local.sh

benchmark:
	PYTHONPATH=src $(PYTHON) scripts/benchmark_planner.py

smoke-live:
	$(PYTHON) scripts/smoke_live.py --base-url $${BASE_URL:-https://qsign.qdev.run} $${REVIEW_TOKEN:+--review-token "$$REVIEW_TOKEN"}
