import discord
from discord.ext import commands
import json
from utils import logger as misolog
from utils import misc as misomisc
import imgkit


def load_data():
    with open('data/users.json', 'r') as filehandle:
        data = json.load(filehandle)
        return data


def save_data(users_json):
    with open('data/users.json', 'w') as filehandle:
        json.dump(users_json, filehandle, indent=4)
        filehandle.close()


badges = {"developer": {"name": "Developer", "description": "Program the bot.", "icon": "fab fa-dev"},
          "patron": {"name": "Patreon Supporter", "description": "Support the development on patreon!",
                     "icon": "fab fa-patreon"},
          "super_hugger": {"name": "Super Hugger", "description": "Hug 10 different people.",
                           "icon": "far fa-smile", "img": "https://i.imgur.com/MbJnCks.png"},
          "best_friend": {"name": "Best Friend", "description": "Hug the same person 10 times.",
                          "icon": "fas fa-heart", "img": "https://i.imgur.com/znHxtP3.png"},
          "master_fisher": {"name": "Master Fisher", "description": "Catch 10k fishy.",
                            "icon": "fas fa-fish", "img": "https://i.imgur.com/spO97nH.png"},
          "lucky_fisher": {"name": "Lucky Fisher", "description": "Catch a legendary fish.",
                           "icon": "fas fa-dragon", "img": "https://i.imgur.com/H7WORY5.png"},
          "generous_fisher": {"name": "Generous Fisher", "description": "Catch 1000 fishy for others.",
                              "icon": "fas fa-hand-holding-heart", "img": "https://i.imgur.com/dcP9XaL.png"}}


class User:

    def __init__(self, client):
        self.client = client
        self.logger = misolog.create_logger(__name__)

    @commands.command()
    async def userinfo(self, ctx):
        """Info about a discord user"""
        self.logger.info(misolog.format_log(ctx, f""))
        users_json = load_data()
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            user = ctx.message.author
        member = ctx.message.guild.get_member(user.id)
        try:
            fishy_amount = users_json['users'][str(user.id)]['fishy']
            timespan = ctx.message.created_at.timestamp() - users_json['users'][str(user.id)]['fishy_timestamp']
            hours = int(timespan // 3600)
            minutes = int(timespan % 3600 // 60)
            fishy_time = f"{hours} hours {minutes} minutes ago"
        except KeyError:
            fishy_amount = 0
            fishy_time = "Never"

        status_emoji = {"online": "<:online:533466178711191590>", "idle": "<:idle:533466151729102852>",
                        "dnd": "<:dnd:533466208377241614>", "offline": "<:offline:533466238567972874>"}
        status = f"{status_emoji[str(member.status)]}{str(member.status).capitalize()}"
        if member.is_on_mobile():
            status += " :iphone:"

        activity = str(member.activities[0]) if member.activities else "None"
        message = discord.Embed(color=user.color)
        message.title = f"{user.name}#{user.discriminator} ({user.id})"
        message.add_field(name="Status", value=status)
        message.add_field(name="Activity", value=activity)
        message.add_field(name="Fishy", value=f":tropical_fish: {fishy_amount}")
        message.add_field(name="Last fishy", value=fishy_time)
        message.add_field(name="Account created", value=user.created_at.strftime('%Y-%m-%d'))
        message.add_field(name="Joined server", value=member.joined_at.strftime('%Y-%m-%d'))
        roles_names = []
        for role in member.roles:
            roles_names.append(role.mention)
        role_string = " ".join([role.mention for role in member.roles])
        message.add_field(name="Roles", value=role_string, inline=False)
        message.set_thumbnail(url=user.avatar_url)

        await ctx.send(embed=message)

    @commands.command()
    async def roleslist(self, ctx, page=1):
        """List the roles of this server"""
        pages = []
        content = discord.Embed(title=f"Roles for {ctx.message.guild.name}")
        content.description = ""
        for role in ctx.message.guild.roles:
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

    @commands.command(name="avatar")
    async def avatar(self, ctx, userid=None):
        """Get a user's profile get"""
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            if userid is not None:
                try:
                    user = ctx.message.guild.get_member(int(userid))
                except Exception:
                    user = None
                if user is None:
                    await ctx.send(f"Couldn't find user {userid}")
                    self.logger.warning(misolog.format_log(ctx, f"Couldn't find user {userid}"))
                    return
            else:
                user = ctx.message.author

        self.logger.info(misolog.format_log(ctx, f"user={user.name}"))

        content = discord.Embed(color=discord.Color.light_grey())
        url = user.avatar_url_as(static_format="png")
        content.set_image(url=url)

        await ctx.send(embed=content)

    @commands.command()
    async def hug(self, ctx, *args):
        """Hug someone"""
        if ctx.message.mentions:
            data = load_data()
            hugged_user = ctx.message.mentions[0]
            await ctx.send(f"{hugged_user.mention} <a:hug:532923159586930700>")

            if str(ctx.message.author.id) not in data['users']:
                data['users'][str(ctx.message.author.id)] = {}
            try:
                data['users'][str(ctx.message.author.id)]['hugs']
            except KeyError:
                data['users'][str(ctx.message.author.id)]['hugs'] = {}
            try:
                data['users'][str(ctx.message.author.id)]['hugs'][str(hugged_user.id)] += 1
            except KeyError:
                data['users'][str(ctx.message.author.id)]['hugs'][str(hugged_user.id)] = 1
            save_data(data)
            # check for badges
            if data['users'][str(ctx.message.author.id)]['hugs'][str(hugged_user.id)] > 9:
                await add_badge(ctx, ctx.message.author, "best_friend")
            if len(data['users'][str(ctx.message.author.id)]['hugs']) > 9:
                await add_badge(ctx, ctx.message.author, "super_hugger")
        else:
            await ctx.send(f"{' '.join(args)} <a:hug:532923159586930700>")

    @commands.command()
    async def profile(self, ctx):
        """Show user profile"""
        if ctx.message.mentions:
            member = ctx.message.mentions[0]
        else:
            member = ctx.message.author

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

        # 1. open file
        with open("html/profile.html", "r", encoding="utf-8") as file:
            html_data = file.read().replace('\n', '')
        # 2. edit it, save file as a copy

        data = load_data()
        with open('data/index.json', 'r') as filehandle:
            leveldata = json.load(filehandle)
        badge_html = ""
        try:
            for badge in data['users'][str(member.id)]['badges']:
                icon = badges[badge]['icon']
                badge_html += f'<i class="badge {icon} fa-2x"></i>'
        except KeyError:
            pass
        try:
            fishy = data['users'][str(ctx.author.id)]['fishy']
        except KeyError:
            fishy = 0
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
        formatted_html = html_data.format(usercolor=usercolor,
                                          avatar_url=avatar_url,
                                          username=username,
                                          discriminator=discriminator,
                                          badge_icons=badge_html,
                                          fishy_amount=fishy,
                                          level_num=level,
                                          xp=f"{leveldata['xp']-misomisc.get_xp(level)}/{misomisc.xp_to_next_level(level)} XP | {leveldata['xp']} XP",
                                          messages_amount=leveldata['messages'],
                                          level_num_g=global_level,
                                          xp_g=f"{global_xp-misomisc.get_xp(global_level)}/{misomisc.xp_to_next_level(global_level)} XP | {global_xp} XP",
                                          messages_amount_g=global_msg
                                          )

        # 3. generate and send
        imgkit.from_string(formatted_html, "downloads/profile.png", options=options, css='html/profile_main.css')
        with open("downloads/profile.png", "rb") as img:
            await ctx.send(file=discord.File(img))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def forcebadge(self, ctx, arg, arg2=""):
        if ctx.message.mentions:
            await add_badge(ctx, ctx.message.mentions[0], arg2, True)
        else:
            try:
                user = self.client.get_user(int(arg))
            except ValueError:
                user = None
            if user is not None:
                await add_badge(ctx, user, arg2, True)
            else:
                await add_badge(ctx, ctx.message.author, arg, True)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def badgetest(self, ctx):
        options = {'quiet': '', 'format': 'png', 'crop-h': "35", 'crop-w': "35"}
        imgkit.from_file("html/badge.html", "downloads/badge.jpeg", options=options)
        with open("downloads/badge.jpeg", "rb") as img:
            await ctx.send(file=discord.File(img))

    @commands.command()
    async def badges(self, ctx):
        """Show a list of your badges"""
        data = load_data()
        try:
            content = f"**{ctx.message.author.display_name}'s badges:**"
            for badge in data['users'][str(ctx.message.author.id)]['badges']:
                content += f"\n{badges[badge]['name']}"
        except KeyError:
            content = "**You have no badges.**"
        await ctx.send(content)


async def add_badge(ctx, user, name, force=False):
    data = load_data()
    userid = str(user.id)
    if 'badges' not in data['users'][userid]:
        data['users'][userid]['badges'] = []
    if name not in data['users'][userid]['badges']:
        data['users'][userid]['badges'].append(name)
    else:
        if not force:
            return
    display_name = badges[name]['name']
    desc = badges[name]['description']
    content = discord.Embed()
    content.description = f":military_medal: **{display_name}**\n"
    content.description += desc
    try:
        content.set_thumbnail(url=badges[name]['img'])
    except KeyError:
        pass
    await ctx.send(f'{user.mention} just earned a new badge!', embed=content)
    save_data(data)


def setup(client):
    client.add_cog(User(client))
