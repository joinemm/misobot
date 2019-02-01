import discord
from discord.ext import commands
import re
import main
from utils import misc

database = main.database


class Notifications:

    def __init__(self, client):
        self.client = client

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
            if word.replace(" ", "") == "":
                await ctx.send("Give me a word to add!")
                return
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
            if word.replace(" ", "") == "":
                await ctx.send("Give me a word to add!")
                return
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
