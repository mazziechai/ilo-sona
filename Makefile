init:
	pdm install
	pdm run pre-commit install

test:
	pdm run pytest -rP ./tests

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs
