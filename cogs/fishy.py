import discord
from discord.ext import commands
import random
import json


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
                rare = random.randint(1, 10) == 1
                amount = random.randint(5, 30)
                if rare:
                    amount = amount*10
                    await ctx.send(f"Caught a rare fish! ({amount} fishies) :blowfish:")
                else:
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



def setup(client):
    client.add_cog(Fishy(client))