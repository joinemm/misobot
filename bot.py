import discord
from discord.ext import commands

TOKEN = "NTAwMzg1ODU1MDcyODk0OTgy.DqKEiQ.4WqACX2kDk7JbzsSQz1KoLErgvk"

client = commands.Bot(command_prefix=">")

extensions = ["commands"]
testing_variable = True

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
