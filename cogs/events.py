import discord
from discord.ext import commands
import re
import traceback
import sys
from utils import logger as misolog
from utils import misc as misomisc
import main

database = main.database


class Events:

    def __init__(self, client):
        self.client = client
        self.delete_log_channel_id = 508668369269162005
        self.log_channel_id = 508668551658471424
        self.logger = misolog.create_logger(__name__)
        self.starred_already = {}

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

    async def on_message(self, message):
        # ignore DMs
        if message.guild is None:
            return

        # ignore own messages
        if message.author == self.client.user:
            return

        # add up and downvotes
        if message.channel.id in database.get_attr("guilds", f"{message.guild.id}.vote_channels", []):
            await message.add_reaction(self.client.get_emoji(540246030491451392))
            await message.add_reaction(self.client.get_emoji(540246041962872852))

        # miso was pinged
        if self.client.user in message.mentions:
            await message.channel.send("<:misoping:532922215105036329>")

        # git gud
        if message.content.startswith("git"):
            gitcommand = re.search(r'git (\S+)', message.content).group(1)
            if gitcommand == "--help":
                await message.channel.send("```\n"
                                           "usage: git [--version] [--help] [-C <path>] [-c <name>=<value>]\n"
                                           "           [--exec-path[=<path>]] [--html-path] [--man-path] [--info-path]\n"
                                           "           [-p | --paginate | --no-pager] [--no-replace-objects] [--bare]\n"
                                           "           [--git-dir=<path>] [--work-tree=<path>] [--namespace=<name>]\n"
                                           "           <command> [<args>]```")
            elif gitcommand == "--version":
                await message.channel.send("git version 2.17.1")
            else:
                await message.channel.send(f"`git: '{gitcommand}' is not a git command. See 'git --help'.`")

        # notifications
        if message.guild is not None:
            triggerwords = database.get_attr("notifications", f"{message.guild.id}")
            if triggerwords is not None:
                triggerwords = list(triggerwords.keys())
                matches = set()
                for word in triggerwords:
                    pattern = re.compile(r'(?:^|\W){0}(?:$|\W)'.format(word), flags=re.IGNORECASE)
                    if pattern.findall(message.content):
                        matches.add(word)
                for word in matches:
                    pattern = re.compile(r'(?:^|\W){0}(?:$|\W)'.format(word), flags=re.IGNORECASE)
                    for user_id in database.get_attr("notifications", f"{message.guild.id}.{word}"):
                        if user_id in database.get_attr("users", f"{user_id}.blacklist", []):
                            return
                        if not user_id == message.author.id:
                            user = message.guild.get_member(user_id)
                            if user is not None:
                                content = discord.Embed()
                                content.set_author(
                                    name=f'{message.author} mentioned "{word}" in {message.guild.name}',
                                    icon_url=message.author.avatar_url)
                                highlighted_text = re.sub(pattern, lambda x: f'**{x.group(0)}**', message.content)
                                content.description = f">>> {highlighted_text}\n\n" \
                                    f"[Go to message]({message.jump_url})"
                                content.set_thumbnail(url=message.guild.icon_url)
                                content.set_footer(text=f"#{message.channel.name}")
                                content.timestamp = message.created_at

                                await user.send(embed=content)

        # xp gain
        xp = misomisc.xp_from_message(message)
        currenthour = message.created_at.hour
        user = database.get_attr("index", f"{message.guild.id}.{message.author.id}")
        if user is None:
            user = {"name": f"{message.author.name}#{message.author.discriminator}",
                    "bot": message.author.bot,
                    "xp": 0,
                    "messages": 0,
                    "activity": [0] * 24}

        level_before = misomisc.get_level(user['xp'])
        user['messages'] += 1
        user['xp'] += xp
        user['activity'][currenthour] += xp
        database.set_attr("index", f"{message.guild.id}.{message.author.id}", user)
        level_now = misomisc.get_level(user['xp'])

        if level_now > level_before:
            if not message.author.bot:
                if database.get_attr("guilds", f"{message.guild.id}.levelup_messages", True):
                    await message.channel.send(f"{message.author.mention} just leveled up! (level **{level_now}**)")

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

    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == "⭐":
            if database.get_attr("guilds", f"{reaction.message.guild.id}.starboard", False):
                if str(reaction.message.id) not in self.starred_already:
                    if reaction.count == database.get_attr("guilds", f"{reaction.message.guild.id}.starboard_amount", 3):

                        channel_id = database.get_attr("guilds", f"{reaction.message.guild.id}.starboard_channel")
                        channel = reaction.message.guild.get_channel(channel_id)
                        if channel is None:
                            return

                        content = discord.Embed(color=discord.Color.gold())
                        content.set_author(name=f"{reaction.message.author}",
                                           icon_url=reaction.message.author.avatar_url)
                        content.description = "<:blank:540269692535963669> " + reaction.message.content + \
                                              f"\n\n[context]({reaction.message.jump_url})"
                        content.timestamp = reaction.message.created_at
                        content.set_footer(text=f"{reaction.count} ⭐ #{reaction.message.channel.name}")
                        if len(reaction.message.attachments) > 0:
                            content.set_image(url=reaction.message.attachments[0].url)

                        mymsg = await channel.send(embed=content)
                        self.starred_already[str(reaction.message.id)] = mymsg.id
                else:
                    channel_id = database.get_attr("guilds", f"{reaction.message.guild.id}.starboard_channel")
                    channel = reaction.message.guild.get_channel(channel_id)
                    if channel is None:
                        return

                    mymsg = await channel.get_message(self.starred_already[str(reaction.message.id)])
                    content = mymsg.embeds[0]
                    content.set_footer(text=f"{reaction.count} ⭐ #{reaction.message.channel.name}")
                    await mymsg.edit(embed=content)

    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command"""

        # This prevents any commands with local handlers being handled here in on_command_error.
        # if hasattr(ctx.command, 'on_error'):
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
            await ctx.send(f"```{type(error)} : {error}```")

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
                result = database.delete_key("guilds", f"{ctx.message.guild.id}.custom_commands.{name}")
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
