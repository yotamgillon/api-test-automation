PY := .venv/bin/python
PYTEST_ARGS ?=
BUGS := BUG-001 BUG-002 BUG-003 BUG-004 BUG-005

.PHONY: install run test test-buggy test-each-bug demo report lint

install:
	python3 -m venv .venv
	$(PY) -m pip install -r requirements.txt
	$(PY) -m playwright install chromium

run:
	$(PY) -m uvicorn app.main:app --port 8000

test:
	$(PY) -m pytest $(PYTEST_ARGS)

test-buggy:
	BUGGY_MODE=1 $(PY) -m pytest $(PYTEST_ARGS)

# Full suite once per seeded bug; failing test ids go to results/by_bug/BUG-00X.txt
test-each-bug:
	mkdir -p results/by_bug
	for bug in $(BUGS); do \
		BUGGY_MODE=$$bug $(PY) -m pytest -q --tb=no -p no:cacheprovider -rf \
			| grep '^FAILED' | sed 's/^FAILED //; s/ - .*//' | sort > results/by_bug/$$bug.txt; \
		echo "$$bug: $$(wc -l < results/by_bug/$$bug.txt | tr -d ' ') failing tests"; \
	done

# Before and after: correct app (must be green), then all bugs on (must fail)
demo:
	$(MAKE) test PYTEST_ARGS="-v --html=results/report_correct.html --self-contained-html" \
		2>&1 | tee results/correct_run.txt
	-$(MAKE) test-buggy PYTEST_ARGS="-v --html=results/report_buggy.html --self-contained-html" \
		2>&1 | tee results/buggy_run.txt

report:
	$(PY) -m pytest --html=results/report.html --self-contained-html \
		--cov=app --cov-branch --cov-report=term-missing --cov-report=html:results/htmlcov
	$(PY) -m coverage report --show-missing > results/coverage.txt
	$(PY) -m coverage json -o results/coverage.json --pretty-print -q

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .
