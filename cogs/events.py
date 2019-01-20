import discord
from discord.ext import commands
import json
import traceback
import sys
from utils import logger as misolog
import main as main


def load_data():
    with open('data/guilds.json', 'r') as filehandle:
        data = json.load(filehandle)
        # print('guilds.json loaded')
        return data


def save_data(guilds_json):
    with open('data/guilds.json', 'w') as filehandle:
        json.dump(guilds_json, filehandle, indent=4)
        # print('guilds.json saved')


class Events:

    def __init__(self, client):
        self.client = client
        self.guilds_json = load_data()
        self.delete_log_channel_id = 508668369269162005
        self.log_channel_id = 508668551658471424
        self.logger = misolog.create_logger(__name__)

    async def on_ready(self):
        """The event triggered when bot is done loading extensions and is ready to use"""
        await self.client.change_presence(activity=discord.Game(name='>info'))
        self.logger.info('Loading complete : Bot state = READY')

    async def on_member_join(self, member):
        """The event triggered when user joins a guild"""
        self.guilds_json = load_data()
        guild = member.guild
        try:
            channel_id = self.guilds_json['guilds'][str(guild.id)]['welcome_channel']
            await self.client.get_channel(channel_id).send(f'Welcome {member.mention}')
            self.logger.info(f"Welcomed {member} to {guild.name}")
        except KeyError:
            self.logger.warning(f"no welcome channel set for {guild.name}")

        try:
            autorole = guild.get_role(self.guilds_json['guilds'][str(guild.id)]['autorole'])
            await member.add_roles(autorole)
        except KeyError:
            self.logger.warning(f"no autorole set for {guild.name}")

    async def on_member_remove(self, member):
        """The event triggered when user leaves a guild"""
        self.guilds_json = load_data()
        guild = str(member.guild.id)
        try:
            channel_id = self.guilds_json['guilds'][guild]['welcome_channel']
            await self.client.get_channel(channel_id).send(f'Goodbye {member.mention}...')
            self.logger.info(f"Said goodbye to {member} from {guild}")
        except KeyError:
            self.logger.warning(f"no welcome channel set for {guild}")

    async def on_message_delete(self, message):
        """The event triggered when a cached message is deleted"""
        ignored_users = [self.client.user.id]
        if message.guild.id in [451832633538772992]:
            if not int(
                    message.author.id) in ignored_users and not message.author.bot and not message.content.startswith(
                    ">"):
                self.logger.info(f'{message.author} Deleted message: "{message.content}"')
                embed = discord.Embed(color=discord.Color.red())
                embed.set_author(name=f"{message.author} in {message.channel.guild.name}",
                                 icon_url=message.author.avatar_url)
                embed.description = message.content
                if len(message.attachments) > 0:
                    embed.set_image(url=message.attachments[0].proxy_url)
                channel = self.client.get_channel(self.delete_log_channel_id)
                await channel.send(embed=embed)

    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command"""

        # This prevents any commands with local handlers being handled here in on_command_error.
        #if hasattr(ctx.command, 'on_error'):
        #    return

        # ignored = commands.CommandNotFound

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, commands.CommandNotFound):
            custom_command = ctx.message.content[1:]
            response = self.custom_command_check(custom_command, ctx)
            if response is not None:
                self.logger.info(misolog.format_log(ctx, f"Custom command"))
                return await ctx.send(response)
            else:
                self.logger.error(misolog.format_log(ctx, str(error)))
                return
        elif isinstance(error, commands.DisabledCommand):
            self.logger.error(misolog.format_log(ctx, str(error)))
            await ctx.send(f'{ctx.command} has been disabled.')
            return
        elif isinstance(error, commands.NoPrivateMessage):
            self.logger.error(misolog.format_log(ctx, str(error)))
            try:
                return await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except:
                pass
            return
        elif isinstance(error, commands.NotOwner):
            self.logger.error(misolog.format_log(ctx, str(error)))
            await ctx.send("Sorry, only Joinemm#1998 can use this command!")
            return
        else:
            self.logger.error(f'Ignoring exception in command {ctx.command}:')
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            await ctx.send(f"```{error}```")

    def custom_command_check(self, name, ctx):
        try:
            guild_id = str(ctx.message.guild.id)
            response = self.guilds_json['guilds'][guild_id]['custom_commands'][name]
            return response
        except KeyError:
            return None

    @commands.command()
    async def command(self, ctx, mode=None, name=None, *args):
        """Add custom commands"""
        commands_that_exist = []
        for command in self.client.commands:
            commands_that_exist.append(command.name)
        try:
            for command_name in self.guilds_json['guilds'][str(ctx.message.guild.id)]['custom_commands']:
                commands_that_exist.append(command_name)
        except KeyError:
            pass

        if mode == "list":
            found = []
            try:
                for x in self.guilds_json['guilds'][str(ctx.message.guild.id)]['custom_commands']:
                    found.append(f">{x}")
            except KeyError:
                pass
            content = discord.Embed(title=f"{ctx.guild.name} commands")
            if found:
                content.description = "\n".join(found)
            else:
                content.description = "No commands set on this server yet!"
            await ctx.send(embed=content)
            return

        elif mode in ["help", None]:
            help_msg = "`>command add [name] [response]`\n" \
                       "`>command remove [name]`\n" \
                       "`>command search [name]`\n" \
                       "`>command list`"
            await ctx.send(help_msg)
            return

        else:
            if name is None:
                await ctx.send(f"ERROR: Parameter `name` not found")
                return
            if mode == "add":
                if name in commands_that_exist:
                    await ctx.send(f"Sorry, the command `>{name}` already exists!")
                    return
                response = " ".join(args)
                if len(response) < 1:
                    await ctx.send("ERROR: Parameter `response` not found")
                    return
                if not str(ctx.message.guild.id) in self.guilds_json['guilds']:
                    self.guilds_json['guilds'][str(ctx.message.guild.id)] = {'custom_commands': {name: response}}
                else:
                    if 'custom_commands' not in self.guilds_json['guilds'][str(ctx.message.guild.id)]:
                        self.guilds_json['guilds'][str(ctx.message.guild.id)]['custom_commands'] = {}
                    self.guilds_json['guilds'][str(ctx.message.guild.id)]['custom_commands'][name] = response

                await ctx.send(f"Custom command `>{name}` succesfully added")
                save_data(self.guilds_json)

            elif mode == "remove":
                try:
                    del self.guilds_json['guilds'][str(ctx.message.guild.id)]['custom_commands'][name]
                    await ctx.send(f"Custom command `>{name}` succesfully deleted")
                    save_data(self.guilds_json)
                except KeyError:
                    await ctx.send(f"ERROR: Custom command `>{name}` doesn't exist!")

            elif mode == "search":
                found = []
                for a in commands_that_exist:
                    if name in a:
                        found.append(f">{a}")
                content = discord.Embed(title="Search result")
                if found:
                    content.description = "\n".join(found)
                else:
                    content.description = "Found nothing!"
                await ctx.send(embed=content)

            else:
                await ctx.send(f"ERROR: Invalid command `{mode}`")


def setup(client):
    client.add_cog(Events(client))
