import discord
from discord.ext import commands
import json


def load_data():
    with open('guilds.json', 'r') as filehandle:
        data = json.load(filehandle)
        print('guilds.json loaded')
        return data


def save_data(guilds_json):
    with open('guilds.json', 'w') as filehandle:
        json.dump(guilds_json, filehandle, indent=4)
        print('guilds.json saved')


class Events:

    def __init__(self, client):
        self.client = client

    async def on_ready(self):
        await self.client.change_presence(activity=discord.Game(name='>info'))
        print('Bot is ready...')

    async def on_member_join(self, member):
        try:
            guilds_json = load_data()
            guild = str(member.guild.id)
            channel_id = guilds_json['guilds'][guild]['welcome_channel']
            await self.client.get_channel(channel_id).send(f'Hello {member.mention}')
        except KeyError:
            print(f"no welcome channel set for {guild}")

    async def on_member_remove(self, member):
        try:
            guilds_json = load_data()
            guild = str(member.guild.id)
            channel_id = guilds_json['guilds'][guild]['welcome_channel']
            await self.client.get_channel(channel_id).send(f'Goodbye {member.mention}...')
        except KeyError:
            print(f"no welcome channel set for {guild}")


def setup(client):
    client.add_cog(Events(client))
