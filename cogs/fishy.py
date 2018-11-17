import discord
from discord.ext import commands
import random
import json
from datetime import datetime


def load_data():
    with open('users.json', 'r') as filehandle:
        data = json.load(filehandle)
        print('users.json loaded')
        return data


def save_data(users_json):
    with open('users.json', 'w') as filehandle:
        json.dump(users_json, filehandle, indent=4)
        print('users.json saved')
        filehandle.close()


class Fishy:

    def __init__(self, client):
        self.client = client

    @commands.command(name="fishy")
    async def fishy(self, ctx):
        user_id = str(ctx.message.author.id)
        timestamp = ctx.message.created_at.timestamp()
        cooldown = 3600
        users_json = load_data()
        if user_id not in users_json['users']:
            users_json['users'][user_id] = {}
        try:
            time_since_fishy = timestamp - users_json['users'][user_id]['fishy_timestamp']
        except KeyError:
            time_since_fishy = cooldown+1
        if time_since_fishy > cooldown:
            trash = random.randint(1, 10) == 1
            if trash:
                users_json['users'][user_id]['fishy_timestamp'] = timestamp
                save_data(users_json)
                await ctx.send(f"Caught trash!  :boot: Better luck next time.")
            else:
                rand = random.randint(1, 100)
                if rand < 5:
                    # rare
                    amount = random.randint(10, 50) * 10
                    await ctx.send(f":star: **Caught a super rare fish! :star: ({amount} fishies)** :tropical_fish:")
                elif rand < 20:
                    # uncommon
                    amount = random.randint(10, 33)*3
                    await ctx.send(f"Caught an uncommon fish! ({amount} fishies) :blowfish:")
                else:
                    amount = random.randint(5, 33)
                    await ctx.send(f"Caught {amount} fishies! :fishing_pole_and_fish: ")
                try:
                    users_json['users'][user_id]['fishy'] += amount
                except KeyError:
                    users_json['users'][user_id]['fishy'] = amount
                users_json['users'][user_id]['fishy_timestamp'] = timestamp
                save_data(users_json)
        else:
            wait_time = cooldown - time_since_fishy
            await ctx.send(f"You can't fish yet, fool! Please wait {int(wait_time/60)} minutes.")

    @commands.command()
    @commands.is_owner()
    async def fishyreset(self, ctx, *args):
        try:
            user_id = args[0]
        except IndexError:
            user_id = str(ctx.message.author.id)

        users_json = load_data()
        users_json['users'][user_id]['fishy_timestamp'] = 0
        save_data(users_json)

    @commands.command()
    async def leaderboard(self, ctx):
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
        for elem in leaderboard:
            message += f"\n{elem[0]} - {elem[1]} fishy"
        await ctx.send(message)

    @commands.command()
    async def profile(self, ctx):
        users_json = load_data()
        user_id = str(ctx.message.author.id)
        member = ctx.message.guild.get_member(int(user_id))
        user_name = self.client.get_user(int(user_id)).name
        author = ctx.message.author
        try:
            fishy_amount = users_json['users'][user_id]['fishy']
            timespan = ctx.message.created_at.timestamp() - users_json['users'][user_id]['fishy_timestamp']
            hours = int(timespan//3600)
            minutes = int(timespan%3600//60)
            fishy_time = f"{hours} hours {minutes} minutes ago"
        except KeyError:
            fishy_amount = 0
            fishy_time = "Never"

        message = discord.Embed(color=author.color)
        if member.nick is not None:
            message.title = f"{member.nick} ({user_name})"
        else:
            message.title = user_name
        message.description = user_id
        message.add_field(name="Fishy", value=fishy_amount)
        message.add_field(name="Last fishy", value=fishy_time)
        message.add_field(name="Account created", value=author.created_at.strftime('%Y-%m-%d'))
        message.add_field(name="Joined server", value=member.joined_at.strftime('%Y-%m-%d'))
        roles_names = []
        for role in member.roles:
            roles_names.append(role.mention)
        role_string = " ".join(roles_names)
        message.add_field(name="Roles", value=role_string)
        message.set_thumbnail(url=author.avatar_url)

        await ctx.send(embed=message)


def setup(client):
    client.add_cog(Fishy(client))
