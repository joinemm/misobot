import discord
from discord.ext import commands
import json


def load_data():
    with open('guilds.json', 'r') as filehandle:
        data = json.load(filehandle)
        # print('guilds.json loaded')
        return data


def save_data(guilds_json):
    with open('guilds.json', 'w') as filehandle:
        json.dump(guilds_json, filehandle, indent=4)
        # print('guilds.json saved')


class Mod:

    def __init__(self, client):
        self.client = client
        self.guilds_json = load_data()

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, time=None):
        """Mute the given user"""
        try:
            muterole = ctx.message.guild.get_role(self.guilds_json['guilds'][str(ctx.message.guild.id)]['muterole'])
            member = ctx.message.mentions[0]
            await member.add_roles(muterole)
            await ctx.send(f"Muted {member.name} ({member.id})")
        except KeyError:
            await ctx.send(f"Muterole not set, please use >set muterole")
        except IndexError:
            await ctx.send(f"Give me someone to mute!")


    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, time=None):
        """Unmute the given user"""
        try:
            muterole = ctx.message.guild.get_role(self.guilds_json['guilds'][str(ctx.message.guild.id)]['muterole'])
            member = ctx.message.mentions[0]
            await member.remove_roles(muterole)
            await ctx.send(f"Unmuted {member.name} ({member.id})")
        except KeyError:
            await ctx.send(f"Muterole not set, please use >set muterole")
        except IndexError:
            await ctx.send(f"Give me someone to unmute!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set(self, ctx, mode, arg=None):
        """Set bot parameters like welcome channel and mute role"""
        guild = str(ctx.guild.id)
        if mode == "welcome":
            if arg is not None:
                welcome_channel = int(arg)
                if guild in self.guilds_json['guilds']:
                    self.guilds_json['guilds'][guild]['welcome_channel'] = welcome_channel
                else:
                    self.guilds_json['guilds'][guild] = {'welcome_channel': welcome_channel}

                await ctx.send(f"Welcome channel for {ctx.guild.name} saved as {welcome_channel}")
            else:
                await ctx.send(f"Error: Please give a channel id to set the welcome channel to")

        elif mode == "muterole":
            muterole_id = ctx.message.role_mentions[0].id
            if guild not in self.guilds_json['guilds']:
                self.guilds_json['guilds'][guild] = {}
            self.guilds_json['guilds'][guild]['muterole'] = muterole_id

            await ctx.send(f"Mute role for {ctx.guild.name} saved as {muterole_id}")
        elif mode == "test":
            await ctx.send(f"{arg} :: {ctx.message.role_mentions}")
        else:
            await ctx.send("Error: Please give something to set")

        save_data(self.guilds_json)
        self.guilds_json = load_data()


def setup(client):
    client.add_cog(Mod(client))
