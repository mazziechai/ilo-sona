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

dev: 
	docker compose up

db:
	# bot must be running
	docker exec -it ilo-sona-bot-1 bash -c 'sqlite3 $${SQLITE_DB}'

dbexport:
	docker cp $(shell docker ps | grep ilo-sona-bot | awk '{print $$1}'):/project/db/ ./db
