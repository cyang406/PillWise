.PHONY: setup test lint fmt app scenarios scenarios-real ddinter check

setup:            ## create venv deps + editable install
	pip install -r requirements.txt && pip install -e .

test:             ## all tests (contract + scenarios + role tests)
	pytest

lint:
	ruff check .

fmt:
	ruff check --fix . && ruff format .

app:              ## run the UI (mock mode unless PILLWISE_MOCK=0)
	streamlit run app/Home.py

scenarios:        ## demo scenarios in current mode
	python scripts/run_scenarios.py

scenarios-real:   ## demo scenarios through the real pipeline
	PILLWISE_MOCK=0 python scripts/run_scenarios.py

ddinter:          ## build data/ddinter.sqlite from data/raw/ddinter/*.csv
	python scripts/load_ddinter.py

check: lint test scenarios   ## what every commit / merge must pass
