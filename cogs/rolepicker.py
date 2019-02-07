from discord.ext import commands
from utils import misc
import main

database = main.database


class Roles:

    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def rolesetup(self, ctx, action=None, name=None, role=None):
        if action == "help":
            await ctx.send("**Usage:** `>rolesetup [add | remove] [name] [role id]`")
            return

        if name is None or len(name) < 1:
            await ctx.send("Invalid name!")
            return

        if action == "add":
            role = misc.role_from_mention(ctx.guild, role)
            if role is None:
                await ctx.send("Invalid Role!")
                return
            database.set_attr("guilds", f"{ctx.guild.id}.roles.{name}", role.id)
            await ctx.send(f"New role **{role.name}** added to picker as `{name}`")

        elif action == "remove":
            database.delete_key("guilds", f"{ctx.guild.id}.roles.{name}")
            await ctx.send(f"Removed `{name}` from picker")

        else:
            await ctx.send("Invalid command! use `add` or `remove`")

    @commands.command()
    async def role(self, ctx, rolename=None):
        roleid = database.get_attr("guilds", f"{ctx.guild.id}.roles.{rolename.strip('+-')}")
        if roleid is None:
            await ctx.send(f"Role `{rolename}` does not exist!")
            return

        role = ctx.guild.get_role(roleid)
        if rolename[0] == "+":
            await ctx.author.add_roles(role)
            await ctx.send(f"Added you the role **{role.name}!**")
        elif rolename[0] == "-":
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the role **{role.name}** from you!")
        else:
            await ctx.send("Invalid syntax! Usage: `>role +name | >role -name`")


def setup(client):
    client.add_cog(Roles(client))
