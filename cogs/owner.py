from discord.ext import commands
import json


def load_data():
    with open('guilds.json', 'r') as filehandle:
        data = json.load(filehandle)
        print('guilds.json loaded')
        return data


def save_data():
    with open('guilds.json', 'w') as filehandle:
        json.dump(guilds_json, filehandle, indent=4)
        print('guilds.json saved')


class Owner:

    def __init__(self, client):
        self.client = client
        self.guilds_json = load_data()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def say(self, ctx, *args):
        print(f"{ctx.message.author} >say {args}")
        channel_id = int(args[0])
        string = " ".join(args[1:])
        channel = self.client.get_channel(channel_id)
        await channel.send(string)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def set(self, ctx, *args):
        try:
            if args[0] == "welcome":
                try:
                    welcome_channel = int(args[1])
                    if str(ctx.guild.id) in self.guilds_json['guilds']:
                        self.guilds_json['guilds'][ctx.guild.id]['welcome_channel'] = welcome_channel
                    else:
                        self.guilds_json['guilds'][ctx.guild.id] = {'welcome_channel': welcome_channel}
                    save_data()
                    await ctx.send(f"Welcome channel for {ctx.guild.id} saved as {welcome_channel}")
                except Exception as e:
                    await ctx.send("argument error args[1]: " + str(e))
        except Exception as e:
            await ctx.send("argument error args[0]: " + str(e))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def logout(self, ctx):
        print(f"{ctx.message.author} >logout")
        print('logout')
        await ctx.send("Logging out... :wave:")
        await self.client.logout()


def setup(client):
    client.add_cog(Owner(client))
