# ilo sona

A utility bot for the [kama sona Discord server](https://discord.gg/ChC6qtVsSE).

## Usage

This project is managed by [Poetry](https://python-poetry.org).

First, make a configuration file as `config.py`:

```
import logging

TOKEN = "token"
LOG_LEVEL = logging.INFO
DB_CONNECTION_STRING = "mongodb://localhost:27017/ilo?retryWrites=true&w=majority"
TEST_SERVERS = [1234]
```

Now, you can run the bot.

```
poetry run python -m ilo
```

If you wish to work on the project, use this command first to install the pre-commit hooks:
```
poetry run pre-commit install
```
