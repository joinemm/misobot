import discord
from discord.ext import commands
import traceback
import sys
from utils import logger as misolog
import main

database = main.database


class Events:

    def __init__(self, client):
        self.client = client
        self.delete_log_channel_id = 508668369269162005
        self.log_channel_id = 508668551658471424
        self.logger = misolog.create_logger(__name__)

    async def on_ready(self):
        """The event triggered when bot is done loading extensions and is ready to use"""
        await self.client.change_presence(activity=discord.Game(name='>info'))
        self.logger.info('Loading complete : Bot state = READY')

    async def on_member_join(self, member):
        """The event triggered when user joins a guild"""
        channel_id = database.get_attr("guilds", f"{member.guild.id}.welcome_channel")
        if channel_id is not None:
            await self.client.get_channel(channel_id).send(f'Welcome {member.mention}')
            self.logger.info(f"Welcomed {member} to {member.guild.name}")
        else:
            self.logger.warning(f"no welcome channel set for {member.guild.name}")

        role_id = database.get_attr("guilds", f"{member.guild.id}.autorole")
        if role_id is not None:
            autorole = member.guild.get_role(role_id)
            await member.add_roles(autorole)
        else:
            self.logger.warning(f"no autorole set for {member.guild.name}")

    async def on_member_remove(self, member):
        """The event triggered when user leaves a guild"""
        channel_id = database.get_attr("guilds", f"{member.guild.id}.welcome_channel")
        if channel_id is not None:
            await self.client.get_channel(channel_id).send(f'Goodbye {member.mention}...')
            self.logger.info(f"Said goodbye to {member} from {member.guild.name}")
        else:
            self.logger.warning(f"no goodbye channel set for {member.guild.name}")

    async def on_message_delete(self, message):
        """The event triggered when a cached message is deleted"""
        channel_id = database.get_attr("guilds", f"{message.guild.id}.log_channel")
        if channel_id is not None:
            if not message.author.bot and not message.content.startswith(">"):
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
            custom_command = ctx.message.content.strip(">").split(" ")[0]
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
            except Exception:
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
        response = database.get_attr("guilds", f"{ctx.message.guild.id}.custom_commands.{name}")
        return response

    @commands.command()
    async def command(self, ctx, mode=None, name=None, *args):
        """Add custom commands"""
        commands_that_exist = []
        for command in self.client.commands:
            commands_that_exist.append(command.name)
            commands_that_exist += command.aliases

        for command_name in database.get_attr("guilds", f"{ctx.message.guild.id}.custom_commands", []):
            commands_that_exist.append(command_name)

        if mode == "list":
            found = []
            for x in database.get_attr("guilds", f"{ctx.message.guild.id}.custom_commands", []):
                found.append(f">{x}")

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

                database.set_attr("guilds", f"{ctx.message.guild.id}.custom_commands.{name}", response)
                await ctx.send(f"Custom command `>{name}` succesfully added")

            elif mode == "remove":
                result = database.del_attr("guilds", f"{ctx.message.guild.id}.custom_commands.{name}")
                if result is True:
                    await ctx.send(f"Custom command `>{name}` succesfully deleted")
                else:
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
