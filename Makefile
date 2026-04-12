# Тесты: интерпретатор из локального venv (см. .cursor/rules/pytest-venv.mdc)
ifeq ($(OS),Windows_NT)
  PY := .venv/Scripts/python.exe
else
  PY := .venv/bin/python
endif

.PHONY: help install-dev test test-v test-vv _require_pytest_cov test-cov test-cov-html test-junit test-lf test-failed-first

help:
	@echo Targets:
	@echo   make install-dev       - pip install -e ".[dev]" (pytest-cov и прочие dev-зависимости)
	@echo   make test              - pytest -q (краткий вывод)
	@echo   make test-v            - pytest -v
	@echo   make test-vv           - pytest -vv + короткий traceback
	@echo   make test-cov          - покрытие в терминале (нужен: make install-dev)
	@echo   make test-cov-html     - покрытие + HTML-отчёт в htmlcov/ (нужен: make install-dev)
	@echo   make test-junit        - JUnit XML в test-results.xml
	@echo   make test-lf           - только упавшие с прошлого прогона
	@echo   make test-failed-first - сначала упавшие, затем остальные

test:
	$(PY) -m pytest -q

test-v:
	$(PY) -m pytest -v

test-vv:
	$(PY) -m pytest -vv --tb=short

install-dev:
	$(PY) -m pip install -e ".[dev]"

# pytest-cov входит в optional-dependencies dev; без него флаги --cov не распознаются
_require_pytest_cov:
	@$(PY) -c "import importlib.util,sys; s=importlib.util.find_spec('pytest_cov'); sys.exit(0 if s else (print('pytest-cov не установлен. Выполните: make install-dev', file=sys.stderr) or 1))"

test-cov: _require_pytest_cov
	$(PY) -m pytest -q --cov=ruzclient --cov-report=term-missing

test-cov-html: _require_pytest_cov
	$(PY) -m pytest -q --cov=ruzclient --cov-report=term-missing --cov-report=html

test-junit:
	$(PY) -m pytest -q --junitxml=test-results.xml

test-lf:
	$(PY) -m pytest -q --lf

test-failed-first:
	$(PY) -m pytest -q --failed-first
