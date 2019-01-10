import discord
from discord.ext import commands
import json
import re


def load_data():
    with open('data/notifications.json', 'r') as filehandle:
        return json.load(filehandle)


def save_data(data):
    with open('data/notifications.json', 'w') as filehandle:
        json.dump(data, filehandle, indent=4)


class Notifications:

    def __init__(self, client):
        self.client = client
        self.notifications_json = load_data()

    async def on_message(self, message):
        if not message.author == self.client.user:
            # miso was pinged
            if self.client.user in message.mentions:
                await message.channel.send("<:misoping:532922215105036329>")

            # notifications
            if message.guild is not None:
                if str(message.guild.id) in self.notifications_json:
                    triggerwords = list(self.notifications_json[str(message.guild.id)].keys())
                    matches = set()
                    for word in triggerwords:
                        match = re.compile(r'(?:^|\W){0}(?:$|\W)'.format(word), flags=re.IGNORECASE)
                        if match.findall(message.content):
                            matches.add(word)
                    for word in matches:
                        for user_id in self.notifications_json[str(message.guild.id)][word]:
                            if not user_id == message.author.id:
                                user = message.guild.get_member(user_id)
                                if user is not None:
                                    content = discord.Embed()
                                    content.set_author(name=f'{message.author} mentioned "{word}" in {message.guild.name}',
                                                       icon_url=message.author.avatar_url)
                                    content.description = f">>> {message.content.replace(word, f'**{word}**')}\n\n" \
                                                          f"[Go to message]({message.jump_url})"
                                    content.set_thumbnail(url=message.guild.icon_url)
                                    #content.add_field(name="[Click here to jump to message]", value=f"http://discordapp.com/channels/{message.guild.id}/{message.channel.id}/{message.id}")

                                    await user.send(embed=content)
                                    #await user.send(f"**{message.author.name}** mentioned `{word}` in **{message.guild.name}**/{message.channel.mention}\n"
                                    #                f">>> {message.content.replace(word, f'**{word}**')}\n"
                                    #                f">>> http://discordapp.com/channels/{message.guild.id}/{message.channel.id}/{message.id}\n")

    @commands.command()
    async def notification(self, ctx, mode, *args):
        if mode == "help":
            content = "`>notification add [word]`\n" \
                      "`>notification remove [word]`\n" \
                      "`>notification list`"
            await ctx.send(content)
            return

        elif mode == "add":
            await ctx.message.delete()
            word = " ".join(args)
            guild = str(ctx.guild.id)
            user = ctx.author.id
            if guild not in self.notifications_json:
                self.notifications_json[guild] = {}
            if word not in self.notifications_json[guild]:
                self.notifications_json[guild][word] = [user]
            else:
                if user in self.notifications_json[guild][word]:
                    await ctx.send("You already have this notification <:hyunjinwtf:532922316212928532>")
                    return
                self.notifications_json[guild][word].append(user)
            save_data(self.notifications_json)
            await ctx.author.send(f"New notification for keyword `{word}` set for `{ctx.guild.name}` ")
            await ctx.send("Set a notification! Check your DMs <:vivismirk:532923084026544128>")
            self.notifications_json = load_data()

        elif mode == "remove":
            await ctx.message.delete()
            word = " ".join(args)
            guild = str(ctx.guild.id)
            user = ctx.author.id
            try:
                self.notifications_json[guild][word].remove(user)
                if len(self.notifications_json[guild][word]) == 0:
                    del self.notifications_json[guild][word]
                save_data(self.notifications_json)
                await ctx.author.send(f"Notification for keyword `{word}` removed for `{ctx.guild.name}` ")
                await ctx.send("removed a notification! Check your DMs <:vivismirk:532923084026544128>")
                self.notifications_json = load_data()
            except KeyError:
                await ctx.send("You don't even have this notification <:hyunjinwtf:532922316212928532>")

        elif mode == "list":
            user = ctx.author.id
            text = ""
            words = {}
            for guild in self.notifications_json:
                for word in self.notifications_json[guild]:
                    if user in self.notifications_json[guild][word]:
                        if guild in words:
                            words[guild].append(word)
                        else:
                            words[guild] = [word]

            for guild in words:
                text += f"{self.client.get_guild(int(guild)).name}:"
                for word in words[guild]:
                    text += f"\n- {word}"
                text += "\n"
            await ctx.author.send(f"```{text}```")
            await ctx.send("List sent to your DMs <:vivismirk:474641574803013638>")

        else:
            await ctx.send(f"Unknown argument `{mode}`")


def setup(client):
    client.add_cog(Notifications(client))
