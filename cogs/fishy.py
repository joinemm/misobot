import discord
from discord.ext import commands
import random
import json
from miso_utils import logger as misolog


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


class Fishy:

    def __init__(self, client):
        self.client = client
        self.logger = misolog.create_logger(__name__)

    @commands.command(name="fishy")
    async def fishy(self, ctx):
        """Go fishing and receive random amount of fishies"""
        user_id_fisher = str(ctx.message.author.id)
        if ctx.message.mentions:
            self_fishy = False
            user_id_receiver = str(ctx.message.mentions[0].id)
        else:
            self_fishy = True
            user_id_receiver = user_id_fisher
        receiver_name = ctx.message.guild.get_member(int(user_id_receiver)).name
        timestamp = ctx.message.created_at.timestamp()
        cooldown = 3600
        users_json = load_data()
        if user_id_fisher not in users_json['users']:
            users_json['users'][user_id_fisher] = {}
        if user_id_receiver not in users_json['users']:
            users_json['users'][user_id_receiver] = {}
        try:
            time_since_fishy = timestamp - users_json['users'][user_id_fisher]['fishy_timestamp']
        except KeyError:
            time_since_fishy = cooldown+1

        if time_since_fishy > cooldown:
            trash = random.randint(1, 10) == 1
            if trash:
                trash_icons = [':moyai:', ':stopwatch:', ':wrench:', ':hammer:', ':pick:', ':nut_and_bolt:', ':gear:',
                               ':toilet:', ':alembic:', ':bathtub:', ':paperclip:', ':scissors:', ':boot:',
                               ':high_heel:', ':spoon:', ':saxophone:', ':trumpet:', ':scooter:', ':anchor:'
                               ]
                rarity = "trash"
                amount = 0
                icon = random.choice(trash_icons)
                if self_fishy:
                    await ctx.send(f"Caught **trash!**  {icon} Better luck next time.")
                else:
                    await ctx.send(f"Caught **trash**  {icon} for {receiver_name}! Better luck next time.")

            else:
                rand = random.randint(1, 100)
                if rand == 1:
                    rarity = "legendary"
                    amount = random.randint(400, 750)
                    if self_fishy:
                        await ctx.send(f":star2: **Caught a *legendary* fish! Congratulations!! :star2: ({amount} fishies)** :dolphin:")
                    else:
                        await ctx.send(f":star2: **Caught a *legendary* fish for {receiver_name}!! :star2: ({amount} fishies)** :dolphin:")

                elif rand < 5:
                    rarity = "rare"
                    amount = random.randint(100, 399)
                    if self_fishy:
                        await ctx.send(f":star: **Caught a super rare fish! :star: ({amount} fishies)** :tropical_fish:")
                    else:
                        await ctx.send(f":star: **Caught a super rare fish for {receiver_name}! :star: ({amount} fishies)** :tropical_fish:")

                elif rand < 20:
                    rarity = "uncommon"
                    amount = random.randint(30, 99)
                    if self_fishy:
                        await ctx.send(f"**Caught an uncommon fish!** (**{amount}** fishies) :blowfish:")
                    else:
                        await ctx.send(f"**Caught an uncommon fish for {receiver_name}!** (**{amount}** fishies) :blowfish:")

                else:
                    rarity = "common"
                    amount = random.randint(1, 29)
                    if amount == 1:
                        if self_fishy:
                            await ctx.send(f"Caught only **{amount}** fishy! :fishing_pole_and_fish:")
                        else:
                            await ctx.send(f"Caught only **{amount}** fishy for {receiver_name}! :fishing_pole_and_fish:")

                    else:
                        if self_fishy:
                            await ctx.send(f"Caught **{amount}** fishies! :fishing_pole_and_fish: ")
                        else:
                            await ctx.send(f"Caught **{amount}** fishies for {receiver_name}! :fishing_pole_and_fish:")
            try:
                users_json['users'][user_id_receiver]['fishy'] += amount
            except KeyError:
                users_json['users'][user_id_receiver]['fishy'] = amount

            if self_fishy is False:
                try:
                    users_json['users'][user_id_fisher]['fishy_gifted'] += amount
                except KeyError:
                    users_json['users'][user_id_fisher]['fishy_gifted'] = amount

            users_json['users'][user_id_fisher]['fishy_timestamp'] = timestamp
            users_json['users'][user_id_fisher]['warning'] = 0

            try:
                users_json['users'][user_id_receiver][f"fish_{rarity}"] += 1
            except KeyError:
                users_json['users'][user_id_receiver][f"fish_{rarity}"] = 1

            save_data(users_json)

            if self_fishy:
                self.logger.info(misolog.format_log(ctx, f"success [{amount}] ({rarity})"))
            else:
                self.logger.info(misolog.format_log(ctx, f"success [gift for {receiver_name}] [{amount}] ({rarity})"))

        else:
            wait_time = cooldown - time_since_fishy
            try:
                warning = users_json['users'][user_id_fisher]['warning']
            except KeyError:
                warning = 0

            if int(wait_time/60) > 0:
                time = f"{int(wait_time/60)} minutes"
            else:
                time = f"{int(wait_time)} seconds."

            if warning == 0:
                await ctx.send(f"You can't fish yet, fool! Please wait {time}.")
            elif warning == 1:
                await ctx.send(f"I already told you, not yet! :angry: Please wait {time}.")
            elif warning == 2:
                await ctx.send(f"You really don't learn do you? :thinking: just wait {time}...")
            elif warning > 2:
                await ctx.send(f"Just wait {time} ok...")
            else:
                await ctx.send(f"{time}")

            try:
                users_json['users'][user_id_fisher]['warning'] += 1
            except KeyError:
                users_json['users'][user_id_fisher]['warning'] = 1
            save_data(users_json)

            self.logger.info(misolog.format_log(ctx, f"fail (wait_time={wait_time:.3f}s)"))


    @commands.command()
    @commands.is_owner()
    async def fishyreset(self, ctx, user_id=None):
        """Reset the fishy cooldown for given user"""
        self.logger.info(misolog.format_log(ctx, f""))
        if user_id is None:
            user_id = str(ctx.message.author.id)

        users_json = load_data()
        users_json['users'][user_id]['fishy_timestamp'] = 0
        save_data(users_json)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def fishyremove(self, ctx, amount):
        """Remove {amount} fishy (for debug use only)"""
        self.logger.info(misolog.format_log(ctx, f""))
        user_id = str(ctx.message.author.id)
        users_json = load_data()
        users_json['users'][user_id]['fishy'] -= int(amount)
        save_data(users_json)

    @commands.command()
    async def leaderboard(self, ctx):
        """The fishy leaderboard"""
        self.logger.info(misolog.format_log(ctx, f""))
        leaderboard = {}
        users_json = load_data()
        for user in users_json['users']:
            try:
                userdata = users_json['users'][user]
                leaderboard[self.client.get_user(int(user)).name] = userdata['fishy']
            except KeyError:
                continue
        leaderboard = sorted(leaderboard.items(), reverse=True, key=lambda x: x[1])
        message = f"**Fishy leaderboard:**"
        ranking = 1
        for elem in leaderboard[:9]:
            if ranking < 4:
                rank_icon = [':first_place:', ':second_place:', ':third_place:'][ranking-1]
                message += f"\n{rank_icon} {elem[0]} - {elem[1]} fishy"
            else:
                message += f"\n{ranking}. {elem[0]} - {elem[1]} fishy"
            ranking += 1
        message += f"\n+ {len(leaderboard[9:])} more users"
        await ctx.send(message)

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
            hours = int(timespan//3600)
            minutes = int(timespan%3600//60)
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
        url = user.avatar_url
        content.set_image(url=url)

        await ctx.send(embed=content)


def setup(client):
    client.add_cog(Fishy(client))
