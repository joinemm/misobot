from discord.ext import commands
import main
import json
from utils import logger as misolog
from utils import sqldatabase
from cogs import database_move

database = main.database


class Owner(commands.Cog):

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
    async def movetosql(self, ctx):
        database_move.full_package()
        await ctx.send("done")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def emojisdb(self, ctx):
        database_move.emojis()

    @commands.command()
    async def commandlist(self, ctx):
        amount = len(self.client.commands)
        s = f"**{amount} commands in total:**"
        for c in self.client.commands:
            s += f"\n>{c.name}"
        await ctx.send(s)


def setup(client):
    client.add_cog(Owner(client))
