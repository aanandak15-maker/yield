# Makefile for API Intensive Testing Framework

.PHONY: help install test test-fast test-slow test-critical test-parallel clean reports

help:
	@echo "API Intensive Testing Framework - Available Commands:"
	@echo ""
	@echo "  make install          - Install test dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-fast        - Run only fast tests"
	@echo "  make test-slow        - Run only slow tests"
	@echo "  make test-critical    - Run only critical tests"
	@echo "  make test-parallel    - Run tests in parallel"
	@echo "  make test-functional  - Run functional tests"
	@echo "  make test-performance - Run performance tests"
	@echo "  make test-load        - Run load and stress tests"
	@echo "  make test-variety-selection-performance - Run variety selection performance tests"
	@echo "  make test-security    - Run security tests"
	@echo "  make locust           - Start Locust web UI for load testing"
	@echo "  make clean            - Clean test artifacts"
	@echo "  make reports          - Open test reports"
	@echo ""

install:
	pip install -r requirements.txt

test:
	pytest -v

test-fast:
	pytest -v -m fast

test-slow:
	pytest -v -m slow

test-critical:
	pytest -v -m critical

test-parallel:
	pytest -v -n auto

test-functional:
	pytest -v -m functional

test-variety-selection:
	pytest -v -m variety_selection

test-validation:
	pytest -v -m validation

test-performance:
	pytest -v -m performance

test-variety-selection-performance:
	pytest -v suites/test_performance.py::TestVarietySelectionPerformance

test-load:
	pytest -v -m load

test-error-handling:
	pytest -v -m error_handling

test-security:
	pytest -v -m security

test-integration:
	pytest -v -m integration

test-backward-compat:
	pytest -v -m backward_compat

test-end-to-end:
	pytest -v -m end_to_end

clean:
	rm -rf .pytest_cache
	rm -rf __pycache__
	rm -rf reports/*.html
	rm -rf reports/*.xml
	rm -rf reports/*.json
	rm -rf reports/*.log
	rm -rf reports/coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

reports:
	@if [ -f reports/test_report.html ]; then \
		open reports/test_report.html || xdg-open reports/test_report.html || start reports/test_report.html; \
	else \
		echo "No test report found. Run 'make test' first."; \
	fi

coverage:
	pytest --cov=test_api_intensive --cov-report=html:reports/coverage --cov-report=term-missing

lint:
	flake8 suites/ utils/ --max-line-length=100

format:
	black suites/ utils/ conftest.py

type-check:
	mypy suites/ utils/

quality: lint type-check
	@echo "Code quality checks completed"

locust:
	@echo "Starting Locust web UI..."
	@echo "Open http://localhost:8089 in your browser"
	locust -f suites/test_load.py --host=http://localhost:8000

locust-headless:
	@echo "Running Locust in headless mode..."
	locust -f suites/test_load.py \
		--host=http://localhost:8000 \
		--users 100 \
		--spawn-rate 10 \
		--run-time 5m \
		--headless \
		--html reports/locust_report.html
	@echo "Report saved to reports/locust_report.html"
