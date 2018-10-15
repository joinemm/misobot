import discord
from discord.ext import commands
import json

client = commands.Bot(command_prefix=">")
extensions = ["commands"]

with open("dont commit\keys.txt", "r") as filehandle:
    data = json.load(filehandle)
    TOKEN = data["TOKEN"]


@client.event
async def on_ready():
    await client.change_presence(game=discord.Game(name=">info"))
    print("Bot is ready...")

if __name__ == "__main__":
    for extension in extensions:
        try:
            client.load_extension(extension)
            print(f"{extension} loaded succesfully")
        except Exception as error:
            print(f"Error loading {extension}: [{error}]")

    client.run(TOKEN)
