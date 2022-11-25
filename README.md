# ilo sona

A utility bot for the [kama sona Discord server](https://discord.gg/ChC6qtVsSE).

## Usage

This project is managed by [pdm](https://pdm.fming.dev/latest/)
and deployed with [docker compose](https://docs.docker.com/compose/).

To develop: `make init`

Copy `sample.env` to `.env` and add your `BOT_TOKEN`:

```sh
BOT_TOKEN=YOUR_BOT_TOKEN
LOG_LEVEL=info
TEST_SERVERS=
SQLITE_DB="/project/db/ilo_sona.sqlite"
```

Build/update container: `make build`

Run bot in container: `make up`

Check on bot status: `make logs`

Shut down bot: `make down`

Refresh (useful for dev): `make down build up`

## Commands

- `/config`: Add a record of the current server into the database.
  - Takes challenge channel, approval channel, challenge role, approval role, and current challenge number.
- `/submit`: Pop up a modal to submit a sentence for translation!
- `/start_challenge`: Debug command that begins a challenge.
