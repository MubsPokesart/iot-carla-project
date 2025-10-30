.PHONY: help setup carla_up smoke health determinism_check lint test web build-web

help:
	@echo "Commands:"
	@echo "  setup              : Install dependencies and set up the environment."
	@echo "  carla_up           : Helper to launch CARLA."
	@echo "  smoke              : Run a smoke test."
	@echo "  health             : Check the health of the CARLA server."
	@echo "  determinism_check  : Run a determinism check."
	@echo "  lint               : Run linters."
	@echo "  test               : Run tests."
	@echo "  web                : Run the web application in development mode."
	@echo "  build-web          : Build the web application."

setup:
	pip install -r requirements.txt
	cd web && npm install
	pre-commit install

carla_up:
	@echo "Please refer to the official CARLA documentation to start the CARLA simulator."
	@echo "https://carla.readthedocs.io/en/latest/getting_started/"

smoke:
	python -m orchestration.runner smoke

health:
	python -m orchestration.runner health

determinism_check:
	python -m orchestration.runner determinism-check

format:
	python -m ruff check --fix .
	python -m black .
	python -m isort .

lint:
	python -m ruff check .
	python -m black --check .
	python -m isort --check .

test:
	pytest -q

web:
	cd web && npm run dev

build-web:
	cd web && npm run build
