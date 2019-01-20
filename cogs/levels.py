import discord
from discord.ext import commands
import json
from utils import misc as misomisc
from utils import logger as misolog
import time as t
from operator import itemgetter


def load_data():
    with open('data/index.json', 'r') as filehandle:
        data = json.load(filehandle)
        return data


def save_data(data):
    with open('data/index.json', 'w') as filehandle:
        json.dump(data, filehandle, indent=4)
        filehandle.close()


class Levels:

    def __init__(self, client):
        self.client = client
        self.level_index = load_data()
        self.logger = misolog.create_logger(__name__)

    @commands.is_owner()
    @commands.command(name="index")
    async def index_messages(self, ctx, arg=None):
        """Index the server for past level stats"""
        self.logger.info(misolog.format_log(ctx, f""))
        if ctx.author.id not in [133311691852218378]:
            await ctx.send(f"You are not authorized to use this command")
            return
        timer = t.time()
        if arg == "server":
            channels = ctx.guild.text_channels
        else:
            channels = [ctx.channel]
        msg = await ctx.send(f"indexing... (0/{len(channels)})")
        num = 0
        self.level_index[str(ctx.guild.id)] = {}
        total_messages = 0
        for channel in channels:
            num += 1
            try:
                messages = await channel.history(limit=None).flatten()
                for message in messages:
                    user = message.author
                    xp = misomisc.xp_from_message(message)
                    currenthour = message.created_at.hour
                    if str(user.id) not in self.level_index[str(ctx.guild.id)]:
                        self.level_index[str(ctx.guild.id)][str(user.id)] = {
                            "name": f"{user.name}#{user.discriminator}",
                            "bot": user.bot,
                            "xp": xp,
                            "messages": 1,
                            "activity": [0] * 24}
                    else:
                        self.level_index[str(ctx.guild.id)][str(user.id)]['xp'] += xp
                        self.level_index[str(ctx.guild.id)][str(user.id)]['messages'] += 1
                        self.level_index[str(message.guild.id)][str(message.author.id)]['activity'][currenthour] += xp
                        total_messages += 1

                await msg.edit(content=f"indexing... ({num}/{len(channels)}) :: total {total_messages} messages from "
                f"{len(self.level_index[str(ctx.guild.id)])} users")
            except Exception:
                await ctx.send(f"Unexpected error indexing channel <#{channel.id}>")
        save_data(self.level_index)
        time_taken = t.time() - timer
        await msg.edit(content=f"indexing... ({num}/{len(channels)}) DONE ({time_taken:.1f}s) :: "
                               f"total {total_messages} messages from {len(self.level_index[str(ctx.guild.id)])} users")

    @commands.command()
    async def level(self, ctx, userid=None):
        """Get your level, or level of userid"""
        self.logger.info(misolog.format_log(ctx, f""))
        exp = load_data()
        if userid is None:
            user = exp[str(ctx.guild.id)][str(ctx.message.author.id)]
        else:
            user = exp[str(ctx.guild.id)][userid]
        level = misomisc.get_level(user['xp'])
        await ctx.send(f"{user['name']} - level {level} | {user['xp']-misomisc.get_xp(level)}"
                       f"/{misomisc.xp_to_next_level(level)} xp to next level (total xp: {user['xp']})")

    @commands.command()
    async def toplevels(self, ctx, scope=None):
        """Get top levels for this server or globally"""
        self.logger.info(misolog.format_log(ctx, f""))
        tops = {}
        for guild in self.level_index:
            if not scope == "global":
                guild = str(ctx.guild.id)
            for userid in self.level_index[guild]:
                userdata = self.level_index[guild][userid]
                if userid not in tops:
                    tops[userid] = {'xp': userdata['xp'], 'messages': userdata['messages']}
                else:
                    tops[userid]['xp'] += userdata['xp']
                    tops[userid]['messages'] += userdata['messages']
            if not scope == "global":
                break

        if not scope == "global":
            content = discord.Embed(title=f"{ctx.guild.name} levels leaderboard")
        else:
            content = discord.Embed(title=f"Global levels leaderboard")

        content.description = ""
        i = 0

        for userid, value in sorted(tops.items(), key=lambda x: itemgetter('xp')(x[1]), reverse=True):
            user = self.client.get_user(int(userid))
            if user is None:
                continue
            i += 1
            row = f"\n{i}. Level **{misomisc.get_level(tops[userid]['xp'])}** - {user.mention} " \
                  f"| **{tops[userid]['xp']}** XP - **{tops[userid]['messages']}** messages"
            if len(content.description) + len(row) < 2000:
                content.description += row
            else:
                break
        await ctx.send(embed=content)

    @commands.command()
    async def activity(self, ctx):
        try:
            post_data = self.level_index[str(ctx.guild.id)][str(ctx.author.id)]['activity']
        except KeyError:
            await ctx.send("You have no activity data yet!")
            return

        chart_rows, num_rows = misomisc.generate_graph(post_data, 5, 15)
        chart_rows[0] = chart_rows[0] + (f" {max(post_data)} xp" if max(post_data) > 15 else f" 15 xp")
        chart_rows[-1] = chart_rows[-1] + " 0 xp"
        chart = "\n".join(chart_rows) + "\n" + "\n".join(num_rows)
        message = f"{chart}"
        await ctx.send(f"`Hourly xp gain chart for {ctx.author.name}`\n```{message}```")

    async def on_message(self, message):
        if message.guild is None:
            return
        if str(message.guild.id) not in self.level_index:
            self.level_index[str(message.guild.id)] = {}

        xp = misomisc.xp_from_message(message)
        currenthour = message.created_at.hour
        try:
            user = self.level_index[str(message.guild.id)][str(message.author.id)]
        except KeyError:
            new_user = {"name": f"{message.author.name}#{message.author.discriminator}",
                        "bot": message.author.bot,
                        "xp": 0,
                        "messages": 0,
                        "activity": [0] * 24}
            self.level_index[str(message.guild.id)][str(message.author.id)] = new_user
            user = self.level_index[str(message.guild.id)][str(message.author.id)]

        user['messages'] += 1
        user['xp'] += xp
        user['activity'][currenthour] += xp
        save_data(self.level_index)


def setup(client):
    client.add_cog(Levels(client))
