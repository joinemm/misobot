import discord
from discord.ext import commands
import requests
import json


class Chatbot(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.sessions = {}

    async def conversation(self, ctx, user, sentence):

        sentence = sentence.replace(str(self.client.user.mention), "Mitsuku")
        sentence = await commands.clean_content(use_nicknames=False, escape_markdown=True).convert(
                    ctx, sentence)

        sentence = (sentence
                    .replace("miso", "mitsuku")
                    .replace("Miso", "Mitsuku")
                    .replace("@", "")
                    )

        sessionid = self.sessions.get(str(user.id), "")
        data = process_talk(user.id, sentence, sessionid)
        for response in data['responses']:
            await ctx.send(user.mention + " " + response
                           .replace("Mitsuku", "Miso")
                           .replace("mitsuku", "miso")
                           .replace("Mousebreaker", "Joinemm")
                           )

        self.sessions[str(user.id)] = data['sessionid']

    @commands.command()
    async def talk(self, ctx, *, sentence):
        """Use this command, or @mention miso to talk with her"""
        await self.conversation(ctx, ctx.author, sentence)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and self.client.user in message.mentions:
            sentence = message.content

            if message.content.startswith(str(self.client.user.mention)):
                sentence = sentence.replace(str(self.client.user.mention), "").strip()

            elif message.content.startswith(f"<@!{self.client.user.id}>"):
                sentence = sentence.replace(f"<@!{self.client.user.id}>", "").strip()

            await self.conversation(await self.client.get_context(message), message.author, sentence)


def process_talk(user_id, sentence, sessionid):
    url = ("https://miapi.pandorabots.com/talk"
           "?botkey=n0M6dW2XZacnOgCWTp0FRYUuMjSfCkJGgobNpgPv9060_72eKnu3Yl-o1v2nFGtSXqfwJBG2Ros~"
           f"&input={sentence}"
           f"&client_name={user_id}"
           f"&sessionid={sessionid}"
           )

    headers = {"Host": "miapi.pandorabots.com",
               "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
               "Accept": "*/*",
               "Accept-Language": "en,en-US;q=0.5",
               "Accept-Encoding": "gzip, deflate, br",
               "Origin": "https://www.pandorabots.com",
               "DNT": "1",
               "Connection": "keep-alive",
               "Referer": "https://www.pandorabots.com/mitsuku/",
               "Content-Length": "0"}

    response = requests.post(url, headers=headers)
    data = json.loads(response.content.decode('utf-8'))
    return data


def setup(client):
    client.add_cog(Chatbot(client))
