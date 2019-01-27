from discord.ext import commands
from utils import logger as misolog
from utils import database as db
import os

logger = misolog.create_logger(__name__)
database = db.Database()

TOKEN = os.environ.get('MISO_BOT_TOKEN')

client = commands.Bot(command_prefix=">")
extensions = ["cogs.commands", "cogs.owner", "cogs.lastfm", "cogs.apis", "cogs.music", "cogs.events",
              "cogs.fishy", "cogs.mod", "cogs.user", "cogs.sorter", "cogs.notifications", "cogs.levels"]


if __name__ == "__main__":
    for extension in extensions:
        try:
            client.load_extension(extension)
            logger.info(f"{extension} loaded successfully")
        except Exception as error:
            logger.error(f"{extension} loading failed [{error}]")

    client.run(TOKEN)
