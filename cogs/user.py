import discord
from discord.ext import commands
from utils import logger as misolog
from utils import misc as misomisc
from utils import plotter
import imgkit
import main
import random
import cogs.utility as util

database = main.database

badges = database.get_attr("data", "badges")


class User:

    def __init__(self, client):
        self.client = client
        self.logger = misolog.create_logger(__name__)
        with open("html/profile.html", "r", encoding="utf-8") as file:
            self.profile_html = file.read().replace('\n', '')

    @commands.command()
    async def userinfo(self, ctx, mention=None):
        """Info about a discord user"""
        self.logger.info(misolog.format_log(ctx, f""))
        if mention is not None:
            user = misomisc.user_from_mention(ctx.guild, mention, ctx.author)
            if user is None:
                user = ctx.author
        else:
            user = ctx.author

        fishy_amount = database.get_attr("users", f"{user.id}.fishy", 0)
        last_fishy = database.get_attr("users", f"{user.id}.fishy_timestamp")
        if last_fishy is not None:
            timespan = ctx.message.created_at.timestamp() - last_fishy
            hours = int(timespan // 3600)
            minutes = int(timespan % 3600 // 60)
            fishy_time = f"{hours} hours {minutes} minutes ago"
        else:
            fishy_time = "Never"

        status_emoji = {"online": "<:online:533466178711191590>", "idle": "<:idle:533466151729102852>",
                        "dnd": "<:dnd:533466208377241614>", "offline": "<:offline:533466238567972874>"}
        status = f"{status_emoji[str(user.status)]}{str(user.status).capitalize()}"
        if user.is_on_mobile():
            status += " :iphone:"

        member_number = 1
        for member in ctx.guild.members:
            if member.joined_at < user.joined_at:
                member_number += 1

        activity = str(user.activities[0]) if user.activities else "None"
        message = discord.Embed(color=user.color)
        message.title = f"{user.name}#{user.discriminator} ({user.id})"
        message.add_field(name="Status", value=status)
        message.add_field(name="Activity", value=activity)
        message.add_field(name="Fishy", value=f":tropical_fish: {fishy_amount}")
        message.add_field(name="Last fishy", value=fishy_time)
        message.add_field(name="Account created", value=user.created_at.strftime('%Y-%m-%d'))
        message.add_field(name="Joined server", value=user.joined_at.strftime('%Y-%m-%d'))
        message.add_field(name="Member", value=f"#{member_number}")
        roles_names = []
        for role in user.roles:
            roles_names.append(role.mention)
        role_string = " ".join([role.mention for role in user.roles])
        message.add_field(name="Roles", value=role_string, inline=False)
        message.set_thumbnail(url=user.avatar_url)

        await ctx.send(embed=message)

    @commands.command()
    async def roleslist(self, ctx, page=1):
        """List the roles of this server"""
        self.logger.info(misolog.format_log(ctx, f""))
        pages = []
        content = discord.Embed(title=f"Roles for {ctx.message.guild.name}")
        content.description = ""
        for role in reversed(ctx.message.guild.roles):
            item = f"{role.mention} ({role.id}) ({str(role.color)}) - {len(role.members)} members\n"
            if len(content.description) + len(item) > 2000:
                pages.append(content)
                content = discord.Embed(title=f"Roles for {ctx.message.guild.name}")
                content.description = ""
            else:
                content.description += item
        pages.append(content)
        if len(pages) > 1:
            pages[int(page) - 1].set_footer(text=f"page {page} of {len(pages)}")

        await ctx.send(embed=pages[int(page)-1])

    @commands.command()
    async def members(self, ctx):
        """Get the members who first joined this server"""
        self.logger.info(misolog.format_log(ctx, f""))
        sorted_members = sorted(ctx.guild.members, key=lambda x: x.joined_at)

        content = discord.Embed(title=f"{ctx.guild.name} Members:")
        description = ""
        pages = []
        y = 0
        for i, member in enumerate(sorted_members):
            if y > 14:
                pages.append(description)
                description = ""
                y = 0
            description += f"\n**#{i+1}** : **{member.name}** ({member.joined_at.strftime('%Y-%m-%d | %H:%M')})"
            y += 1

        pages.append(description)
        content.description = pages[0]
        if len(pages) > 1:
            content.set_footer(text=f"page 1 of {len(pages)}")
        my_msg = await ctx.send(embed=content)

        if len(pages) > 1:
            await util.page_switcher(self.client, my_msg, content, pages)

    @commands.command()
    async def serverinfo(self, ctx):
        """Info about the server"""
        self.logger.info(misolog.format_log(ctx, f""))

        message = discord.Embed(color=int(misomisc.get_color(ctx.guild.icon_url), 16))
        message.title = f"{ctx.guild.name} | #{ctx.guild.id}"
        message.add_field(name="Owner", value=f"{ctx.guild.owner.name}#{ctx.guild.owner.discriminator}")
        message.add_field(name="Region", value=str(ctx.guild.region))
        message.add_field(name="Created At", value=ctx.guild.created_at.strftime('%Y-%m-%d | %H:%M'))
        message.add_field(name="Members", value=str(ctx.guild.member_count))
        message.add_field(name="Roles", value=str(len(ctx.guild.roles)))
        message.add_field(name="Emojis", value=str(len(ctx.guild.emojis)))
        message.add_field(name="Channels", value=f"{len(ctx.guild.text_channels)} Text channels, "
                                                 f"{len(ctx.guild.voice_channels)} Voice channels")
        message.set_thumbnail(url=ctx.guild.icon_url)

        await ctx.send(embed=message)

    @commands.command(name="avatar")
    async def avatar(self, ctx, mention=None, extra=None):
        """Get a user's profile picture"""
        self.logger.info(misolog.format_log(ctx, f""))
        if mention is not None:
            user = misomisc.user_from_mention(ctx.guild, mention, ctx.author)
            if user is None:
                user = ctx.author
        else:
            user = ctx.author

        self.logger.info(misolog.format_log(ctx, f"user={user.name}"))

        if extra == "png" or mention == "png":
            avatar_url = user.avatar_url_as(static_format="png", format="png")
        else:
            avatar_url = user.avatar_url_as(static_format="png")

        content = discord.Embed(color=user.color)
        content.set_author(name=f"{user.name}", url=avatar_url)
        content.set_image(url=avatar_url)

        await ctx.send(embed=content)

    @commands.command()
    async def hug(self, ctx, *args):
        """Hug someone"""
        text = []
        users = []
        for arg in args:
            user = misomisc.user_from_mention(self.client, arg)
            if user is not None:
                text.append(user.mention)
                users.append(user)
            else:
                text.append(arg)
        owned_badges = database.get_attr("users", f"{ctx.author.id}.badges", [])
        for user in users:
            database.set_attr("users", f"{ctx.author.id}.hugs.{user.id}", 1, increment=True)
            if "best_friend" not in owned_badges:
                if database.get_attr("users", f"{ctx.author.id}.hugs.{user.id}") > 9:
                    await add_badge(ctx, ctx.message.author, "best_friend")

        emojis = database.get_attr("data", "hug_emojis", ["`problem loading emojis`"])
        await ctx.send(f"{' '.join(text)} {random.choice(emojis)}")

        if "super_hugger" not in owned_badges:
            if len(database.get_attr("users", f"{ctx.author.id}.hugs")) > 9:
                await add_badge(ctx, ctx.message.author, "super_hugger")

    @commands.command()
    async def profile(self, ctx, mention=None):
        """Show user profile"""
        if mention is not None:
            member = misomisc.user_from_mention(ctx.guild, mention, ctx.author)
            if member is None:
                member = ctx.author
        else:
            member = ctx.author

        usercolor = str(ctx.message.guild.get_member(member.id).color)
        avatar_url = member.avatar_url_as(static_format="png", size=128)
        username = member.display_name
        discriminator = "#" + member.discriminator

        # config = imgkit.config(wkhtmltoimage='/usr/bin/wkhtmltopdf')
        options = {
            'format': 'png',
            'crop-h': '350',
            'crop-w': '500',
            'crop-x': '0',
            'crop-y': '0',
            'xvfb': '',
            'quiet': ''
        }

        leveldata = database.get_attr("index", ".")
        badge_html = ""
        for badge in database.get_attr("users", f"{member.id}.badges", []):
            icon = badges[badge]['icon']
            badge_html += f'<i class="badge {icon} fa-2x"></i>'
        fishy = database.get_attr("users", f"{member.id}.fishy", 0)

        # plotter.create_graph(leveldata[str(ctx.guild.id)][str(ctx.author.id)]['activity'])

        global_xp = 0
        global_msg = 0
        for guild in leveldata:
            try:
                global_xp += leveldata[guild][str(ctx.author.id)]['xp']
                global_msg += leveldata[guild][str(ctx.author.id)]['messages']
            except KeyError:
                pass
        global_level = misomisc.get_level(global_xp)
        leveldata = leveldata[str(ctx.guild.id)][str(ctx.author.id)]
        level = misomisc.get_level(leveldata['xp'])
        xps = f"{leveldata['xp']-misomisc.get_xp(level)}/{misomisc.xp_to_next_level(level)} XP | {leveldata['xp']} XP"
        xpsg = f"{global_xp-misomisc.get_xp(global_level)}/{misomisc.xp_to_next_level(global_level)} XP | {global_xp} XP"
        formatted_html = self.profile_html.format(
              usercolor=usercolor,
              avatar_url=avatar_url,
              username=username,
              discriminator=discriminator,
              badge_icons=badge_html,
              fishy_amount=fishy,
              level_num=level,
              xp=xps,
              messages_amount=leveldata['messages'],
              level_num_g=global_level,
              xp_g=xpsg,
              messages_amount_g=global_msg
              )

        # 3. generate and send
        imgkit.from_string(formatted_html, "downloads/profile.png", options=options, css='html/profile_main.css')
        with open("downloads/profile.png", "rb") as img:
            await ctx.send(file=discord.File(img))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def forcebadge(self, ctx, mention, name):
        if mention is not None:
            user = misomisc.user_from_mention(self.client, mention, ctx.author)
            if user is None:
                user = ctx.author
        else:
            user = ctx.author
        await add_badge(ctx, user, name, True)

    @commands.command()
    async def badges(self, ctx):
        """Show a list of your badges"""
        userbadges = database.get_attr("users", f"{ctx.author.id}.badges")
        if userbadges is None:
            content = "**You have no badges.**"
        else:
            content = f"**{ctx.message.author.display_name}'s badges:**"
            for badge in userbadges:
                content += f"\n{badges[badge]['name']}"
        await ctx.send(content)


async def add_badge(ctx, user, name, force=False):
    response = database.append_attr("users", f"{user.id}.badges", name, duplicate=False)
    if response or force:
        display_name = badges[name]['name']
        desc = badges[name]['description']
        content = discord.Embed()
        content.description = f":military_medal: **{display_name}**\n"
        content.description += desc
        content.set_thumbnail(url=badges[name].get("img"))
        await ctx.send(f'{user.mention} just earned a new badge!', embed=content)


def setup(client):
    client.add_cog(User(client))
