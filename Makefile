.PHONY: dev test lint up down

up:
	docker compose up --build

down:
	docker compose down

test:
	cd backend && pytest -q

dev:
	docker compose up db -d
	@echo "Run backend and frontend in separate terminals."
