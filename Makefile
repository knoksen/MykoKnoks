.PHONY: dev test lint up down ingest-fast load-store

up:
	docker compose up --build

down:
	docker compose down

test:
	cd backend && pytest -q

dev:
	docker compose up db -d
	@echo "Run backend and frontend in separate terminals."

lint:
	cd backend && ruff check app tests

ingest-fast:
	python scripts/ingest_live_features.py --lat 58.735 --lon 5.647 --radius-km 1 --fast --out data/jaren-fast.jsonl

load-store:
	python scripts/load_feature_store.py data/jaren-fast.jsonl
