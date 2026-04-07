.PHONY: install test report clean

install:
	pip install -r requirements.txt

test:
	pytest

test-verbose:
	pytest -v -s

report:
	allure generate reports/allure-results -o reports/allure-report --clean
	allure open reports/allure-report

clean:
	rm -rf reports/allure-results reports/allure-report .pytest_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
