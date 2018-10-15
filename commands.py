import json
import random as rd
import re
import urllib.parse
import urllib.request
import discord
import requests
import wikipedia as wp
from discord.ext import commands
from lxml import html

with open("dont commit\keys.txt", "r") as filehandle:
    data = json.load(filehandle)
    WEATHER_TOKEN = data["WEATHER_API"]

class Commands:
    def __init__(self, client):
        self.client = client
        with open("artists.txt", "r") as filehandle:
            self.artists = json.load(filehandle)
            print("artists.txt loaded succesfully")

    @commands.command()
    async def info(self):
        # help_string = "```I am Miso Bot, created by Joinemm. Use >help for a list of commands```"
        # await self.client.say(help_string)

        info_embed = discord.Embed(
            title="Hello",
            description="I am Miso Bot, created by Joinemm. Use >help for a list of commands",
            colour=discord.Colour.magenta()
        )

        info_embed.set_footer(text="version 0.04")

        # info_embed.set_image(
        #    url="")
        info_embed.set_thumbnail(
            url=self.client.user.avatar_url)
        # info_embed.set_author(name="author name", icon_url=self.client.user.avatar_url)
        info_embed.add_field(name="Github", value="https://github.com/joinemm/Miso-Bot", inline=False)

        await self.client.say(embed=info_embed)

    @commands.command(pass_context=True)
    async def ping(self, ctx):
        pong_msg = await self.client.say(":ping_pong:")
        ms = (pong_msg.timestamp - ctx.message.timestamp).total_seconds() * 1000
        await self.client.edit_message(pong_msg, new_content=f":ping_pong: {ms}ms")

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
        if args[0] == "random":
            search_string = wp.random()
        else:
            search_string = " ".join(args)
        try:
            page = wp.page(search_string)
            await self.client.say(page.url)
        except wp.exceptions.DisambiguationError as error:
            print(error)
            await self.client.say("```" + str(error) + "```")

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

    @commands.command()
    async def stan(self, *args):
        if args:
            if args[0] == "update":
                amount = len(self.artists)
                print(f"Updating artists.txt... current amount of artists is {amount}")
                self.artists = []
                urls_to_scrape = ["https://kprofiles.com/k-pop-girl-groups/",
                                  "https://kprofiles.com/k-pop-boy-groups/",
                                  "https://kprofiles.com/co-ed-groups-profiles/",
                                  "https://kprofiles.com/kpop-duets-profiles/",
                                  "https://kprofiles.com/kpop-solo-singers/"
                                  ]
                for url in urls_to_scrape:
                    self.artists += scrape_kprofiles(url)

                print(f"Artist list updated. new amount of artists is {len(self.artists)}")
                with open("artists.txt", "w") as filehandle:
                    json.dump(self.artists, filehandle)
                    print("New artists succesfully dumped to artists.txt")
                    await self.client.say(f"Artist list succesfully updated, {len(self.artists)-amount} new entries, "
                                          f"{len(self.artists)} total entries")
                return

            elif args[0] == "clear":
                print("Clearing artist list...")
                self.artists = []
                with open("artists.txt", "w") as filehandle:
                    json.dump(self.artists, filehandle)
                    print("Artist list cleared")
                    await self.client.say("Artist list succesfully cleared")
                return

        try:
            artist = str(rd.choice(self.artists))
            await self.client.say("stan " + artist)
            print(f"selected {artist} out of {len(self.artists)} artists")
        except IndexError:
            error = "Error: artist list is empty, please use >stan update"
            print(error)
            await self.client.say(error)

    @commands.command()
    async def weather(self, *args):
        try:
            city = " ".join(args)
            response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_TOKEN}")
            weather_data = json.loads(response.content.decode('utf-8'))
            weather = weather_data["weather"][0]["main"]
            await self.client.say(f"Weather in {city}: {weather}")
        except Exception as error:
            await self.client.say(f"Error: {error}")
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

    TODO: Weather command, spotify api, lastfm(?), 
    """


def scrape_kprofiles(url):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    results = tree.xpath('//article/div/div/div/p/a[@href]/text()')
    filtered_results = []
    discarded_results = 0
    for item in results:
        if item in ["\n", " "]:
            discarded_results += 1
            continue
        else:
            if "Profile" in item:
                item = item.replace("Profile", "")
            filtered_results.append(item.strip())
    print(f"discarded {discarded_results} results")
    return filtered_results


def setup(client):
    client.add_cog(Commands(client))
