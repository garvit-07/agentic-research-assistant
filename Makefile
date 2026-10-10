.PHONY: install run test lint format ingest docker-build docker-up docker-down

install:
	pip install -r requirements.txt -r requirements-dev.txt

run:
	uvicorn app.main:app --reload --port 8000

test:
	pytest -q

lint:
	ruff check .

format:
	ruff check --fix . && ruff format .

ingest:
	python -m scripts.ingest

docker-build:
	docker compose build

docker-up:
	docker compose up --build

docker-down:
	docker compose down
