from discord.ext import commands


class Owner:

    def __init__(self, client):
        self.client = client

    @commands.command(hidden=True)
    @commands.is_owner()
    async def say(self, ctx, *args):
        """Make the bot say something in a give channel"""
        print(f"{ctx.message.author} >say {args}")
        channel_id = int(args[0])
        string = " ".join(args[1:])
        channel = self.client.get_channel(channel_id)
        await channel.send(string)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def guilds(self, ctx):
        content = "**Connected guilds:**\n"
        for guild in self.client.guilds:
            content += f"{guild.name} - {guild.member_count} users\n"
        await ctx.send(content)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def logout(self, ctx):
        """Shut down the bot"""
        print(f"{ctx.message.author} >logout")
        print('logout')
        await ctx.send("Shutting down... :wave:")
        await self.client.logout()


def setup(client):
    client.add_cog(Owner(client))
