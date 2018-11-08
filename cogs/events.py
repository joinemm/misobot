import discord
from discord.ext import commands
import json
import traceback
import sys
import time


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
        self.guilds_json = load_data()
        self.delete_log_channel_id = 508668369269162005
        self.log_channel_id = 508668551658471424

    async def on_ready(self):
        await self.client.change_presence(activity=discord.Game(name='>info'))
        print('Bot is ready...')

    async def on_member_join(self, member):
        try:
            guild = str(member.guild.id)
            channel_id = self.guilds_json['guilds'][guild]['welcome_channel']
            await self.client.get_channel(channel_id).send(f'Hello {member.mention}')
            print(f"Welcomed {member} to {guild}")
        except KeyError:
            print(f"no welcome channel set for {guild}")

    async def on_member_remove(self, member):
        try:
            guild = str(member.guild.id)
            channel_id = self.guilds_json['guilds'][guild]['welcome_channel']
            await self.client.get_channel(channel_id).send(f'Goodbye {member.mention}...')
            print(f"Said goodbye to {member} from {guild}")
        except KeyError:
            print(f"no welcome channel set for {guild}")

    async def on_message_delete(self, message):
        if not int(message.author.id) == self.client.user.id:
            print(f"deleted message by {message.author} in {message.channel.guild.name} logged")
            embed = discord.Embed(color=discord.Color.red())
            embed.set_author(name=f"{message.author} in {message.channel.guild.name}", icon_url=message.author.avatar_url)
            embed.description = message.content

            channel = self.client.get_channel(self.delete_log_channel_id)
            await channel.send(embed=embed)

    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception"""

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        # ignored = commands.CommandNotFound

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, commands.CommandNotFound):
            print(f"{ctx.message} : {error}")
            return
        elif isinstance(error, commands.NotOwner):
            await ctx.send("Sorry, only Joinemm can use this command!")
            return
        else:
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            await ctx.send(f"```{error}```")

        """
        http://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html#errors
        
        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(f'{ctx.command} has been disabled.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except:
                pass

        # For this error example we check to see where it came from...
        # elif isinstance(error, commands.BadArgument):
        #     if ctx.command.qualified_name == 'tag list':  # Check if the command being invoked is 'tag list'
        #         return await ctx.send('I could not find that member. Please try again.')

        # All other Errors not returned come here... And we can just print the default TraceBack.
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)

        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        """


def setup(client):
    client.add_cog(Events(client))
