import discord
from discord.ext import commands


class Owner:

    def __init__(self, client):
        self.client = client

    @commands.command(hidden=True)
    async def say(self, ctx, *args):
        channel_id = int(args[0])
        string = " ".join(args[1:])
        channel = self.client.get_channel(channel_id)
        await channel.send(string)


def setup(client):
    client.add_cog(Owner(client))
