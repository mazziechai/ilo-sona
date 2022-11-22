import logging
from logging.handlers import RotatingFileHandler

import discord
import mongoengine
from config import DB_CONNECTION_STRING, LOG_LEVEL, TEST_SERVERS, TOKEN

from .bot import Ilo


def main():
    if not TOKEN:
        raise Exception("A token was not specified in the config!")

    # Setting up logging
    logging.getLogger("discord").setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    file_handler = RotatingFileHandler(
        filename="bot.log",
        encoding="utf-8",
        mode="w",
        maxBytes=32 * 1024 * 1024,
        backupCount=5,
    )
    datefmt = "%Y-%m-%d %H:%M:%S"
    fmt = logging.Formatter(
        "[{asctime}] [{levelname}] {name}: {message}", datefmt, style="{"
    )

    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    log = logging.getLogger("ilo")

    # Initialize databaseC
    mongoengine.connect(host=DB_CONNECTION_STRING)

    # Actually starting the bot and logging into Discord
    bot = Ilo(
        activity=discord.Activity(type=discord.ActivityType.listening, name="/help"),
        debug_guilds=TEST_SERVERS,
    )

    log.info("Logging in...")
    bot.run(TOKEN, reconnect=True)


if __name__ == "__main__":
    main()
