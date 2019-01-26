import discord
from discord.ext import commands
import re
import main
from utils import misc

database = main.database


class Notifications:

    def __init__(self, client):
        self.client = client

    async def on_message(self, message):
        if message.author == self.client.user:
            # ignore own messages
            return

        # miso was pinged
        if self.client.user in message.mentions:
            await message.channel.send("<:misoping:532922215105036329>")

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
                                content.set_author(name=f'{message.author} mentioned "{word}" in {message.guild.name}',
                                                   icon_url=message.author.avatar_url)
                                highlighted_text = re.sub(pattern, lambda x: f'**{x.group(0)}**', message.content)
                                content.description = f">>> {highlighted_text}\n\n" \
                                                      f"[Go to message]({message.jump_url})"
                                content.set_thumbnail(url=message.guild.icon_url)
                                content.set_footer(text=f"#{message.channel.name}")
                                content.timestamp = message.created_at

                                await user.send(embed=content)

    @commands.command()
    async def notification(self, ctx, mode, *args):
        """Add keywords to get notified when someone mentions them"""
        if mode == "help":
            content = "`>notification add [word]`\n" \
                      "`>notification remove [word]`\n" \
                      "`>notification block [user]`\n" \
                      "`>notification unblock [user]`\n" \
                      "`>notification list`"
            await ctx.send(content)
            return

        elif mode == "add":
            await ctx.message.delete()
            word = " ".join(args)
            if ctx.author.id not in database.get_attr("notifications", f"{ctx.guild.id}.{word}", []):
                database.append_attr("notifications", f"{ctx.guild.id}.{word}", ctx.author.id)
                await ctx.author.send(f"New notification for keyword `{word}` set in `{ctx.guild.name}` ")
                await ctx.send("Set a notification! Check your DMs <:vivismirk:532923084026544128>")
            else:
                await ctx.send("You already have this notification <:hyunjinwtf:532922316212928532>")
                return

        elif mode == "remove":
            await ctx.message.delete()
            word = " ".join(args)
            if ctx.author.id in database.get_attr("notifications", f"{ctx.guild.id}.{word}", []):
                response = database.delete_attr("notifications", f"{ctx.guild.id}.{word}", ctx.author.id)
                if response is True:
                    await ctx.author.send(f"Notification for keyword `{word}` removed for `{ctx.guild.name}` ")
                    await ctx.send("removed a notification! Check your DMs <:vivismirk:532923084026544128>")
                else:
                    await ctx.send("You don't even have this notification <:hyunjinwtf:532922316212928532>")

        elif mode == "list":
            text = ""
            words = {}
            for guild_id in database.get_attr("notifications", ".", []):
                for word in database.get_attr("notifications", f"{guild_id}", []):
                    if ctx.author.id in database.get_attr("notifications", f"{guild_id}.{word}", []):
                        if guild_id in words:
                            words[guild_id].append(word)
                        else:
                            words[guild_id] = [word]

            for guild in words:
                server = self.client.get_guild(int(guild))
                if server is not None:
                    text += f"**{server.name}:**"
                    for word in words[guild]:
                        text += f"\n└`{word}`"
                    text += "\n"
            await ctx.author.send(text)
            await ctx.send("List sent to your DMs <:vivismirk:532923084026544128>")

        elif mode == "block":
            user = misc.user_from_mention(self.client, args[0])
            if user is not None:
                database.append_attr("users", f"{ctx.author.id}.blacklist", user.id)
                await ctx.send(f"User `@{user.name}` is now blocked from notifying you")
            else:
                await ctx.send("ERROR: Invalid user")
        elif mode == "unblock":
            user = misc.user_from_mention(self.client, args[0])
            if user is not None:
                database.delete_attr("users", f"{ctx.author.id}.blacklist", user.id)
                await ctx.send(f"User `@{user.name}` removed from notification blacklist")
            else:
                await ctx.send("ERROR: Invalid user")

        else:
            await ctx.send(f"Unknown argument `{mode}`")


def setup(client):
    client.add_cog(Notifications(client))
