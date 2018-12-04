import discord
from discord.ext import commands
import json
from utils import logger as misolog
import imgkit


def load_data():
    with open('users.json', 'r') as filehandle:
        data = json.load(filehandle)
        # print('users.json loaded')
        return data


def save_data(users_json):
    with open('users.json', 'w') as filehandle:
        json.dump(users_json, filehandle, indent=4)
        # print('users.json saved')
        filehandle.close()


class User:

    def __init__(self, client):
        self.client = client
        self.logger = misolog.create_logger(__name__)

    @commands.command()
    async def profile(self, ctx):
        """User profile"""
        self.logger.info(misolog.format_log(ctx, f""))
        users_json = load_data()
        if ctx.message.mentions:
            user_id = str(ctx.message.mentions[0].id)
            author = ctx.message.mentions[0]
        else:
            user_id = str(ctx.message.author.id)
            author = ctx.message.author
        member = ctx.message.guild.get_member(int(user_id))
        user_name = self.client.get_user(int(user_id)).name
        try:
            fishy_amount = users_json['users'][user_id]['fishy']
            try:
                fishy_gifted = users_json['users'][user_id]['fishy_gifted']
            except KeyError:
                fishy_gifted = 0
            timespan = ctx.message.created_at.timestamp() - users_json['users'][user_id]['fishy_timestamp']
            hours = int(timespan // 3600)
            minutes = int(timespan % 3600 // 60)
            fishy_time = f"{hours} hours {minutes} minutes ago"

            fish_collection = ""
            for fishtype in ['trash', 'common', 'uncommon', 'rare', 'legendary']:
                try:
                    qty = users_json['users'][user_id][f'fish_{fishtype}']
                except KeyError:
                    continue
                fish_collection += f"{fishtype}: {qty}\n"

        except KeyError:
            fishy_amount = 0
            fishy_gifted = 0
            fishy_time = "Never"
            fish_collection = "N/A"

        message = discord.Embed(color=author.color)
        if member.nick is not None:
            message.title = f"{member.nick} ({user_name})"
        else:
            message.title = user_name
        message.description = user_id
        message.add_field(name="Fishy", value=fishy_amount)
        message.add_field(name="Fishy gifted", value=fishy_gifted)
        message.add_field(name="Last fishy", value=fishy_time)
        message.add_field(name="Fish collection", value=fish_collection)
        message.add_field(name="Account created", value=author.created_at.strftime('%Y-%m-%d'))
        message.add_field(name="Joined server", value=member.joined_at.strftime('%Y-%m-%d'))
        roles_names = []
        for role in member.roles:
            roles_names.append(role.mention)
        role_string = " ".join(roles_names)
        message.add_field(name="Roles", value=role_string)
        message.set_thumbnail(url=author.avatar_url)

        await ctx.send(embed=message)

    @commands.command(name="avatar")
    async def avatar(self, ctx, userid=None):
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
    async def profile2(self, ctx):

        member = ctx.message.author

        header_color = str(ctx.message.guild.get_member(member.id).color)
        avatar_url = member.avatar_url_as(static_format="png", size=128)
        username = member.display_name
        discriminator = "#" + member.discriminator

        config = imgkit.config(wkhtmltoimage='C:/Program Files/wkhtmltopdf/bin/wkhtmltoimage.exe')
        options = {
            'format': 'png',
            'crop-h': '350',
            'crop-w': '500',
        }

        # 1. open file
        lines = []
        with open("html/profile.html", "r", encoding="utf-8") as file:
            for line in file:
                lines.append(line.rstrip())
        # 2. edit it, save file as a copy
        with open("html/edited_profile.html", "w", encoding="utf-8") as file:
            for line in lines:
                line = line.replace("$headercolor$", header_color)
                line = line.replace("$avatar_url$", avatar_url)
                line = line.replace("$username$", username)
                line = line.replace("$discriminator$", discriminator)
                print(line, file=file)
                #print(line)
        # 3. generate and send
        imgkit.from_file("html/edited_profile.html", "downloads/profile.png", config=config, options=options)
        with open("downloads/profile.png", "rb") as img:
            await ctx.send(file=discord.File(img))
        # 4. delete

       # with open("html/profile.html", "rb") as f:
        #imgkit.from_file("html/profile.html", "downloads/profile.png", config=config, options=options)



def setup(client):
    client.add_cog(User(client))
