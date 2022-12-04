import logging
import os

import discord

BOT_TOKEN = os.environ["BOT_TOKEN"]
LOG_LEVEL = os.environ["LOG_LEVEL"].upper()
TEST_SERVERS = [int(n) for n in os.environ["TEST_SERVERS"].split(",") if n]
SQLITE_DB = os.environ["SQLITE_DB"]

LOG = logging.getLogger()

from ilo.bot import Ilo


def init_logger():
    logging.getLogger("discord").setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    datefmt = "%Y-%m-%d %H:%M:%S"
    fmt = logging.Formatter(
        "[{asctime}] [{levelname}] {name}: {message}", datefmt, style="{"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    root_logger.addHandler(stream_handler)


def main():
    assert BOT_TOKEN, "A token was not provided in the environment!"
    init_logger()

    bot = Ilo(
        database_file=SQLITE_DB,
        activity=discord.Activity(type=discord.ActivityType.listening, name="/help"),
        debug_guilds=TEST_SERVERS,
    )

    LOG.info("Logging in...")
    bot.run(BOT_TOKEN, reconnect=True)


if __name__ == "__main__":
    main()
