from discord.ext import commands
import main
import json
from utils import logger as misolog
from utils import sqldatabase

database = main.database


class Owner:

    def __init__(self, client):
        self.client = client
        self.logger = misolog.create_logger(__name__)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def say(self, ctx, *args):
        """Make the bot say something in a give channel"""
        self.logger.info(misolog.format_log(ctx, f""))
        channel_id = int(args[0])
        string = " ".join(args[1:])
        channel = self.client.get_channel(channel_id)
        await channel.send(string)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def guilds(self, ctx):
        self.logger.info(misolog.format_log(ctx, f""))
        content = "**Connected guilds:**\n"
        for guild in self.client.guilds:
            content += f"**{guild.name}** - {guild.member_count} users\n"
        await ctx.send(content)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def logout(self, ctx):
        """Shut down the bot"""
        self.logger.info(misolog.format_log(ctx, f""))
        print('logout')
        await ctx.send("Shutting down... :wave:")
        await self.client.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def getvalue(self, ctx, file, path):
        await ctx.send(f"```{json.dumps(database.get_attr(file, path, 'Not Found'), indent=4)}```")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def setvalue(self, ctx, file, path, value):
        if value.startswith("int"):
            value = int(value.strip("int"))
        else:
            value = value.split(",") if len(value.split(",")) > 1 else value
        database.set_attr(file, path, value)
        await ctx.send("ok")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sql(self, ctx, *args):
        command = " ".join(args)
        sqldatabase.execute(f"""{command}""")
        await ctx.send("ok")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sqlquery(self, ctx, *args):
        command = " ".join(args)
        response = sqldatabase.query(f"""{command}""")
        await ctx.send(f"```{response}```")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def convertusersdb(self, ctx):
        usersdb = database.get_attr("users", ".")
        sqldatabase.execute("""CREATE TABLE users (
                            discord_id INTEGER PRIMARY KEY,
                            lastfm_username TEXT,
                            sunsign TEXT,
                            location TEXT
                            );""")

        sqldatabase.execute("""CREATE TABLE fishy (
                            discord_id INTEGER PRIMARY KEY,
                            timestamp FLOAT,
                            fishy INTEGER,
                            fishy_gifted INTEGER,
                            trash INTEGER,
                            common INTEGER,
                            uncommon INTEGER,
                            rare INTEGER,
                            legendary INTEGER,
                            warning INTEGER);""")
        sqldatabase.execute("""CREATE TABLE badges (
                            discord_id INTEGER PRIMARY KEY,
                            developer INTEGER,
                            patron INTEGER,
                            super_hugger INTEGER,
                            best_friend INTEGER,
                            master_fisher INTEGER,
                            lucky_fisher INTEGER,
                            generous_fisher INTEGER);""")

        for userid in usersdb:
            sqldatabase.execute("""INSERT INTO users VALUES (?, ?, ?, ?);""",
                                (int(userid),
                                 usersdb[userid].get("lastfm_username"),
                                 usersdb[userid].get("sunsign"),
                                 None))
            sqldatabase.execute("""INSERT INTO fishy VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (int(userid),
                                 usersdb[userid].get("fishy_timestamp"),
                                 usersdb[userid].get("fishy"),
                                 usersdb[userid].get("fishy_gifted"),
                                 usersdb[userid].get("fish_trash"),
                                 usersdb[userid].get("fish_common"),
                                 usersdb[userid].get("fish_uncommon"),
                                 usersdb[userid].get("fish_rare"),
                                 usersdb[userid].get("fish_legendary"),
                                 usersdb[userid].get("warning")
                                 ))

            badges = usersdb[userid].get("badges")
            if badges is not None:
                sqldatabase.execute("""INSERT INTO badges VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (int(userid),
                                     (1 if "developer" in badges else 0),
                                     (1 if "patron" in badges else 0),
                                     (1 if "super_hugger" in badges else 0),
                                     (1 if "best_friend" in badges else 0),
                                     (1 if "master_fisher" in badges else 0),
                                     (1 if "lucky_fisher" in badges else 0),
                                     (1 if "generous_fisher" in badges else 0),
                                     ))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def notisql(self, ctx):
        notifs = database.get_attr("notifications", ".")
        for guildid in notifs:
            for keyword in notifs[guildid]:
                for userid in notifs[guildid][keyword]:
                    print(guildid, userid, keyword)
                    sqldatabase.execute("REPLACE INTO notifications VALUES (?, ?, ?)", (int(guildid), int(userid), keyword))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def indextosql(self, ctx):
        index = database.get_attr("index", ".")
        for guildid in index:
            for userid in index[guildid]:
                xp = index[guildid][userid]['xp']
                bot = 1 if index[guildid][userid]['bot'] else 0
                messages = index[guildid][userid]['messages']
                activity = index[guildid][userid]['activity']
                values = [int(guildid), int(userid), bot, xp, messages] + activity
                print(values)
                sqldatabase.execute("REPLACE INTO activity VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                                    "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    tuple(values))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def guildsql(self, ctx):
        guilds = database.get_attr("guilds", ".")
        for guild_id in guilds:
            muterole = guilds[guild_id].get('muterole')
            autorole = guilds[guild_id].get('autorole')
            levelup_toggle = guilds[guild_id].get('levelup_messages', True)
            levelup_toggle = 1 if levelup_toggle else 0

            welcome_toggle = guilds[guild_id].get('welcome', True)
            welcome_toggle = 1 if welcome_toggle else 0
            welcome_channel = guilds[guild_id].get('welcome_channel')

            starboard_toggle = guilds[guild_id].get('starboard', False)
            starboard_toggle = 1 if starboard_toggle else 0
            starboard_channel = guilds[guild_id].get('starboard_channel')
            starboard_amount = guilds[guild_id].get('starboard_amount', 3)

            sqldatabase.execute("REPLACE INTO guilds VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (guild_id, muterole, autorole, levelup_toggle, welcome_toggle, welcome_channel, None,
                                 starboard_toggle, starboard_channel, starboard_amount))

            for command in guilds[guild_id].get('custom_commands', []):
                response = guilds[guild_id]['custom_commands'][command]
                sqldatabase.execute("REPLACE INTO customcommands VALUES (?, ?, ?)", (guild_id, command, response))

            for role in guilds[guild_id].get('roles', []):
                role_id = guilds[guild_id]['roles'][role]
                sqldatabase.execute("REPLACE INTO roles VALUES (?, ?, ?)", (guild_id, role, role_id))

            for channel_id in guilds[guild_id].get('vote_channels', []):
                sqldatabase.execute("REPLACE INTO votechannels VALUES (?, ?)", (guild_id, channel_id))

    @commands.command()
    async def commandlist(self, ctx):
        amount = len(self.client.commands)
        s = f"**{amount} commands in total:**"
        for c in self.client.commands:
            s += f"\n>{c.name}"
        await ctx.send(s)


def setup(client):
    client.add_cog(Owner(client))
