from discord.ext import commands
import json
from utils import logger as misolog
import os

logger = misolog.create_logger(__name__)

TOKEN = os.environ.get('MISO_BOT_TOKEN')

client = commands.Bot(command_prefix=">")
extensions = ["cogs.commands", "cogs.owner", "cogs.lastfm", "cogs.apis", "cogs.voice", "cogs.events",
              "cogs.fishy", "cogs.mod", "cogs.user"]


def load_data():
    with open('guilds.json', 'r') as filehandle:
        data = json.load(filehandle)
    return data


def save_data(guilds_json):
    with open('guilds.json', 'w') as filehandle:
        json.dump(guilds_json, filehandle, indent=4)


if __name__ == "__main__":
    for extension in extensions:
        try:
            client.load_extension(extension)
            logger.info(f"{extension} loaded successfully")
        except Exception as error:
            logger.error(f"{extension} loading failed [{error}]")

    client.run(TOKEN)
