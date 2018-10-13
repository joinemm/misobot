import discord
from discord.ext import commands
import urllib.parse
import urllib.request
import re
import wikipedia as wp
import random as rd


class Commands:
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def info(self):
        help_string = "```I am Miso Bot, created by Joinemm. Use >help for a list of commands```"
        await self.client.say(help_string)

    @commands.command()
    async def ping(self):
        await self.client.say("pong")

    @commands.command(pass_context=True)
    async def say(self, ctx, *args):
        content = ""
        for word in args:
            content += word + " "
        await self.client.say(content)
        await self.client.delete_message(ctx.message)

    @commands.command()
    async def random(self, cap=1):
        content = rd.randint(0, int(cap))
        await self.client.say(content)

    @commands.command()
    async def youtube(self, *args):
        search_string = ""
        for word in args:
            search_string += word + " "
        query_string = urllib.parse.urlencode({"search_query": search_string})
        html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
        search_results = re.findall(r'href=\"\/watch\?v=(.{11})', html_content.read().decode())
        result = "http://www.youtube.com/watch?v=" + search_results[0]
        await self.client.say(result)

    @commands.command()
    async def wikipedia(self, *args):
        search_string = ""
        for word in args:
            search_string += word + " "
        page = wp.page(search_string)
        await self.client.say(page.url)

    @commands.command()
    async def navyseal(self):
        copypasta = "What the fuck did you just fucking say about me, you little bitch? " \
                    "I'll have you know I graduated top of my class in the Navy Seals, " \
                    "and I've been involved in numerous secret raids on Al-Quaeda, " \
                    "and I have over 300 confirmed kills. I am trained in gorilla warfare " \
                    "and I'm the top sniper in the entire US armed forces. " \
                    "You are nothing to me but just another target. " \
                    "I will wipe you the fuck out with precision the likes of which has never " \
                    "been seen before on this Earth, mark my fucking words. " \
                    "You think you can get away with saying that shit to me over the Internet? " \
                    "Think again, fucker. As we speak I am contacting my secret network of spies across the USA" \
                    " and your IP is being traced right now so you better prepare for the storm, maggot. " \
                    "The storm that wipes out the pathetic little thing you call your life. " \
                    "You're fucking dead, kid. I can be anywhere, anytime, and I can kill you in over seven hundred ways, " \
                    "and that's just with my bare hands. Not only am I extensively trained in unarmed combat, " \
                    "but I have access to the entire arsenal of the United States Marine Corps and I will use it " \
                    "to its full extent to wipe your miserable ass off the face of the continent, you little shit. " \
                    "If only you could have known what unholy retribution your little clever comment was about to " \
                    "bring down upon you, maybe you would have held your fucking tongue. But you couldn't, you didn't, " \
                    "and now you're paying the price, you goddamn idiot. I will shit fury all over you and you will drown " \
                    "in it. You're fucking dead, kiddo."
        await self.client.say(copypasta)

    """
    @commands.command()
    async def displayembed(self):
        embed = discord.Embed(
            title="Title",
            description="this is a description",
            colour=discord.Colour.magenta()
        )

        embed.set_footer(text="this is a footer")

        embed.set_image(
            url="https://sparkpeo.hs.llnwd.net/e2/guid/Mighty-Miso-Soup-RECIPE/b05f546f-72e9-4661-8cf6-6955b665fcd0.jpg")
        embed.set_thumbnail(
            url="https://sparkpeo.hs.llnwd.net/e2/guid/Mighty-Miso-Soup-RECIPE/b05f546f-72e9-4661-8cf6-6955b665fcd0.jpg")
        embed.set_author(name="author name",
                         icon_url="https://sparkpeo.hs.llnwd.net/e2/guid/Mighty-Miso-Soup-RECIPE/b05f546f-72e9-4661-8cf6-6955b665fcd0.jpg")
        embed.add_field(name="Field name", value="Field value", inline=False)
        embed.add_field(name="Field name", value="Field value", inline=True)
        embed.add_field(name="Field name", value="Field value", inline=True)

        await self.client.say(embed=embed)

    
    TODO: fix permissions (prevent anyone from clearing messages)

    @client.command(pass_context=True)
    async def clear(ctx, amount=2):
        channel = ctx.message.channel
        messages = []
        async for message in client.logs_from(channel, limit=int(amount)):
            messages.append(message)
        await client.delete_messages(messages)


    TODO: make this work (cant get image urls)

    @client.command()
    async def google(*args):
        search_string = ""
        for word in args:
            search_string += word + " "
        query_string = urllib.parse.urlencode({"search_query": search_string})
        url = urllib.request.Request("https://www.google.com/search?q=" + query_string + "&tbm=isch", headers={'User-Agent': 'Mozilla/5.0'})
        html_content = urllib.request.urlopen(url)
        images = re.findall(r'href=\"\/imgres\?imgurl=(.{})', html_content.read().decode())
        print(html_content)

    just some basic tests stuff

    @client.event
    async def on_message(message):
        author = message.author
        content = message.content
        channel = message.channel
        print(f"{author}: {content}")

    @client.event
    async def on_message_delete(message):
        author = message.author
        content = message.content
        channel = message.channel
        await client.send_message(channel, content)
    """


def setup(client):
    client.add_cog(Commands(client))