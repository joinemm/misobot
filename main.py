from discord.ext import commands
import json
from utils import logger as misolog

logger = misolog.create_logger(__name__)

with open('dont commit\\keys.txt', 'r') as filehandle:
    TOKEN = json.load(filehandle)["TOKEN"]

client = commands.Bot(command_prefix=">")
extensions = ["cogs.commands", "cogs.owner", "cogs.lastfm", "cogs.apis", "cogs.voice", "cogs.events",
              "cogs.tictactoe", "cogs.fishy", "cogs.mod", "cogs.user"]

if __name__ == "__main__":
    for extension in extensions:
        try:
            client.load_extension(extension)
            logger.info(f"{extension} loaded successfully")
        except Exception as error:
            logger.error(f"{extension} loading failed [{error}]")

    client.run(TOKEN)
