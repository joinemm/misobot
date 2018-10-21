import discord
from discord.ext import commands


class Events:

    def __init__(self, client):
        self.client = client

    async def on_ready(self):
        await self.client.change_presence(activity=discord.Game(name='>info'))
        print('Bot is ready...')


def setup(client):
    client.add_cog(Events(client))