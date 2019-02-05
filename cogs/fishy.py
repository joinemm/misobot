import discord
from discord.ext import commands
import random
from utils import logger as misolog
from utils import misc as misomisc
import cogs.user as usercog
import main

database = main.database


class Fishy:

    def __init__(self, client):
        self.client = client
        self.logger = misolog.create_logger(__name__)

    @commands.command(name="fishy", aliases=['fisy', 'fsihy', 'fish', 'foshy', 'fihsy', 'fisyh', 'fhisy', '물고기', '랴노ㅛ'])
    async def fishy(self, ctx, *args):
        """Go fishing and receive random amount of fishies"""
        user_id_fisher = ctx.message.author.id
        user_id_receiver = user_id_fisher
        for arg in args:
            user = misomisc.user_from_mention(self.client, arg)
            if user is not None:
                user_id_receiver = user.id
                break
        if user_id_fisher == user_id_receiver:
            self_fishy = True
        else:
            self_fishy = False
        receiver_name = ctx.message.guild.get_member(user_id_receiver).name
        timestamp = ctx.message.created_at.timestamp()
        cooldown = 3600

        time_since_fishy = timestamp - database.get_attr("users", f"{user_id_fisher}.fishy_timestamp", 0)

        korean = ctx.message.content.startswith(">물고기") or ctx.message.content.startswith(">랴노ㅛ")

        if time_since_fishy > cooldown or time_since_fishy is None:
            trash = random.randint(1, 10) == 1
            if trash:
                trash_icons = [':moyai:', ':stopwatch:', ':wrench:', ':hammer:', ':pick:', ':nut_and_bolt:',
                               ':gear:', ':toilet:', ':alembic:', ':bathtub:', ':paperclip:', ':scissors:',
                               ':boot:', ':high_heel:', ':spoon:', ':saxophone:', ':trumpet:', ':scooter:',
                               ':anchor:'
                               ]
                rarity = "trash"
                amount = 0
                icon = random.choice(trash_icons)
                if korean:
                    await ctx.send(f"너는 **쓰레기!**  {icon}" + ("" if self_fishy else f" **{receiver_name}** 를 위해")
                                   + "다음에 잘하면 돼.")
                else:
                    await ctx.send(f"Caught **trash!**  {icon}" + ("" if self_fishy else f" for {receiver_name}")
                                   + " Better luck next time.")

            else:
                rand = random.randint(1, 100)
                if rand == 1:
                    rarity = "legendary"
                    amount = random.randint(400, 750)
                    if korean:
                        await ctx.send(":star2: **너는" + ("" if self_fishy else f" **{receiver_name}** 를 위해") +
                                       f" 전설의 마리의 물고기를 잡았다!! :star2: ({amount} 물고기)** :dolphin:")
                    else:
                        await ctx.send(f":star2: **Caught a *legendary* fish" +
                                       ("" if self_fishy else f" for {receiver_name}") + f"!! :star2: ({amount} "
                                       "fishies)** :dolphin:")

                elif rand < 5:
                    rarity = "rare"
                    amount = random.randint(100, 399)
                    if korean:
                        await ctx.send(":star: **너는" + ("" if self_fishy else f" **{receiver_name}** 를 위해") +
                                       f" 드문 마리의 물고기를 잡았다! :star: ({amount} 물고기)** :tropical_fish:")
                    else:
                        await ctx.send(f":star: **Caught a super rare fish" +
                                       ("" if self_fishy else f" for {receiver_name}") + f"! :star: ({amount} "
                                       "fishies)** :tropical_fish:")

                elif rand < 20:
                    rarity = "uncommon"
                    amount = random.randint(30, 99)
                    if korean:
                        await ctx.send("**너는" + ("" if self_fishy else f" **{receiver_name}** 를 위해") +
                                       f" 보통 아닌 마리의 물고기를 잡았다!** (**{amount}** 물고기) :blowfish:")
                    else:
                        await ctx.send(f"**Caught an uncommon fish " + ("" if self_fishy else f"for {receiver_name}") +
                                       f"!** (**{amount}** fishies) :blowfish:")

                else:
                    rarity = "common"
                    amount = random.randint(1, 29)
                    if amount == 1 and not korean:
                        await ctx.send(f"Caught only **{amount}** fishy " +
                                       ("" if self_fishy else f"for **{receiver_name}**") + "! :fishing_pole_and_fish:")

                    else:
                        if korean:
                            await ctx.send(f"너는" + ("" if self.fishy else f" **{receiver_name}** 를 위해") +
                                           f" **{amount}** 마리의 물고기를 잡았다! :fishing_pole_and_fish:")
                        else:
                            await ctx.send(f"Caught **{amount}** fishies " +
                                           ("" if self.fishy else f"for **{receiver_name}**") +
                                           "! :fishing_pole_and_fish:")

                database.set_attr("users", f"{user_id_receiver}.fishy", amount, increment=True)

                if not self_fishy:
                    database.set_attr("users", f"{user_id_fisher}.fishy_gifted", amount, increment=True)

            database.set_attr("users", f"{user_id_fisher}.fishy_timestamp", timestamp)
            database.set_attr("users", f"{user_id_fisher}.warning", 0)
            database.set_attr("users", f"{user_id_receiver}.fish_{rarity}", 1, increment=True)

            userbadges = database.get_attr("users", f"{user_id_fisher}.badges", default={})
            if self_fishy:
                self.logger.info(misolog.format_log(ctx, f"success [{amount}] ({rarity})"))
                if "master_fisher" not in userbadges:
                    if database.get_attr("users", f"{user_id_fisher}.fishy", default=0) > 9999:
                        await usercog.add_badge(ctx, ctx.message.author, "master_fisher")
            else:
                self.logger.info(misolog.format_log(ctx, f"success [gift for {receiver_name}] [{amount}] ({rarity})"))
                if "generous_fisher" not in userbadges:
                    if database.get_attr("users", f"{user_id_fisher}.fishy_gifted", default=0) > 999:
                        await usercog.add_badge(ctx, ctx.message.author, "generous_fisher")
            if rarity == "legendary" and "lucky_fisher" not in userbadges:
                await usercog.add_badge(ctx, ctx.message.author, "lucky_fisher")

        else:
            wait_time = cooldown - time_since_fishy
            try:
                warning = database.get_attr("users", f"{user_id_fisher}.warning")
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

            database.set_attr("users", f"{user_id_fisher}.warning", 1, increment=True)

            self.logger.info(misolog.format_log(ctx, f"fail (wait_time={wait_time:.3f}s)"))

    @commands.command(aliases=["leaderboards"])
    async def leaderboard(self, ctx, mode=None, page=None):
        """The fishy leaderboard"""
        self.logger.info(misolog.format_log(ctx, f""))
        if mode is not None and page is None:
            try:
                page = int(mode)
            except ValueError:
                page = 1
        if page is None:
            page = 1
        leaderboard = {}
        perpage = 15
        for userid in database.get_attr("users", ".", {}):
            if not mode == "global":
                if ctx.message.guild.get_member(int(userid)) is None:
                    continue
            userdata = database.get_attr("users", f"{userid}")
            if userdata is not None:
                this_user = self.client.get_user(int(userid))
                if this_user is None:
                    continue
                amount = database.get_attr("users", f"{userid}.fishy")
                if amount is not None:
                    leaderboard[this_user.name] = amount
            else:
                continue
        leaderboard = sorted(leaderboard.items(), reverse=True, key=lambda x: x[1])
        message = discord.Embed()
        message.title = f"Fishy leaderboard{'' if page is 1 else f' | page {page}'}:"
        message.description = ""
        toskip = (int(page) - 1) * perpage
        ranking = 1 + toskip
        for elem in leaderboard[toskip:toskip+perpage]:
            if ranking < 4:
                rank_icon = [':first_place:', ':second_place:', ':third_place:'][ranking-1]
                message.description += f"\n{rank_icon} {elem[0]} - **{elem[1]}** fishy"
            else:
                message.description += f"\n**{ranking}.** {elem[0]} - **{elem[1]}** fishy"
            ranking += 1
        message.set_footer(text=f"\n+ {len(leaderboard[toskip+perpage:])} more users")
        await ctx.send(embed=message)

    @commands.command()
    async def fishystats(self, ctx, mention=None):
        """Get total fishing stats"""
        fishy_total = 0
        fishy_gifted_total = 0
        trash = 0
        common = 0
        uncommon = 0
        rare = 0
        legendary = 0
        message = discord.Embed()
        if mention == "global":
            users_to_parse = database.get_attr("users", ".")
            message.title = "Global fishy stats"
        else:
            if mention is not None:
                member = misomisc.user_from_mention(self.client, mention, ctx.author)
            else:
                member = ctx.author
            users_to_parse = [member.id]
            message.title = f"{member.name} fishy stats"
        for user in users_to_parse:
            userdata = database.get_attr("users", f"{user}")
            if userdata is None:
                await ctx.send("User not found in database")
                self.logger.warning(misolog.format_log(ctx, f"UserError"))
                return
            fishy_total += userdata.get("fishy", 0)
            fishy_gifted_total += userdata.get("fishy_gifted", 0)
            trash += userdata.get("fish_trash", 0)
            common += userdata.get("fish_common", 0)
            uncommon += userdata.get("fish_uncommon", 0)
            rare += userdata.get("fish_rare", 0)
            legendary += userdata.get("fish_legendary", 0)

        total = trash+common+uncommon+rare+legendary
        message.description = f"Total fishies fished: **{fishy_total}**\n" \
                              f"Total fishies gifted: **{fishy_gifted_total}**\n\n" \
                              f"Trash: **{trash}** - {(trash/total)*100:.1f}%\n" \
                              f"Common: **{common}** - {(common/total)*100:.1f}%\n" \
                              f"Uncommon: **{uncommon}** - {(uncommon/total)*100:.1f}%\n" \
                              f"Rare: **{rare}** - {(rare/total)*100:.1f}%\n" \
                              f"Legendary: **{legendary}** - {(legendary/total)*100:.1f}%\n\n" \
                              f"Total fish count: **{total}**\n" \
            f"Average fishy: **{fishy_total / total:.2f}**"
        await ctx.send(embed=message)
        self.logger.info(misolog.format_log(ctx, f""))

    @commands.command(disabled=True, hidden=True)
    async def presents(self, ctx, option):
        amount = database.get_attr("users", f"{ctx.author.id}.fish_gift", 0)
        if amount == 0:
            await ctx.send("You don't have any presents!")
            return
        if option == "open":
            pass
        elif option == "gift":
            try:
                recipent = ctx.message.mentions[0]
            except IndexError:
                await ctx.send("Please mention someone to gift to")
                return
            database.set_attr("users", f"{ctx.author.id}.fish_gift", -1, increment=True)
            database.set_attr("users", f"{recipent.id}.fish_gift", 1, increment=True)

        else:
            await ctx.send(f"You have {amount} unopened presents. "
                           f"use `>presents open` to open one or `>presents gift` to give one to someone else")


def setup(client):
    client.add_cog(Fishy(client))
