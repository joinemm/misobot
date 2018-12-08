from __future__ import unicode_literals
import json
import random as rd
import re
import discord
import requests
import wikipedia as wp
from discord.ext import commands
from lxml import html
import urllib.parse
import time
from utils import logger as misolog
from bs4 import BeautifulSoup
import youtube_dl
import os


def load_data():
    with open('data.json', 'r') as filehandle:
        data = json.load(filehandle)
        # print('data.json loaded')
        return data


def save_data():
    with open('data.json', 'w') as filehandle:
        json.dump(data_json, filehandle, indent=4)
        # print('data.json saved')


data_json = load_data()


class Commands:

    def __init__(self, client):
        self.client = client
        self.start_time = time.time()
        self.artists = data_json['artists']
        self.logger = misolog.create_logger(__name__)

    @commands.command()
    async def website(self, ctx):
        await ctx.send("http://joinemm.me/misobot/")

    @commands.command(name='info')
    async def info(self, ctx):
        """Get information about the bot"""
        self.logger.info(misolog.format_log(ctx, f""))
        info_embed = discord.Embed(title='Hello',
                                   description='I am Miso Bot, created by Joinemm. Use >help for a list of commands.'
                                               f'\n\nCurrently active in {len(self.client.guilds)} servers.',
                                   colour=discord.Colour.magenta())

        info_embed.set_footer(text='version 0.7.1')
        info_embed.set_thumbnail(url=self.client.user.avatar_url)
        info_embed.add_field(name='Github', value='https://github.com/joinemm/Miso-Bot', inline=False)
        info_embed.add_field(name='Documentation', value="http://joinemm.me/misobot", inline=False)

        await ctx.send(embed=info_embed)

    @commands.command(name='ping')
    async def ping(self, ctx):
        """Get the bot's ping"""
        pong_msg = await ctx.send(":ping_pong:")
        ms = (pong_msg.created_at - ctx.message.created_at).total_seconds() * 1000
        await pong_msg.edit(content=f":ping_pong: {ms}ms")
        self.logger.info(misolog.format_log(ctx, f"ping={ms}ms"))

    @commands.command(name="uptime")
    async def uptime(self, ctx):
        """Get the bot's uptime"""
        up_time = time.time() - self.start_time
        m, s = divmod(up_time, 60)
        h, m = divmod(m, 60)
        await ctx.send("Current process uptime: %d hours %d minutes %d seconds" % (h, m, s))
        self.logger.info(misolog.format_log(ctx, f"uptime={up_time}"))

    @commands.command(name='random')
    async def rng(self, ctx, _range=1):
        """Gives random integer from 0 to given input"""
        content = rd.randint(0, int(_range))
        await ctx.send(content)
        self.logger.info(misolog.format_log(ctx, f"range=[0,{_range}], result={content}"))

    @commands.command(name='youtube')
    async def youtube(self, ctx, *args):
        """Search youtube for the given search query and return first result"""
        search_string = " ".join(args)
        search_string = urllib.parse.urlencode({'search_query': search_string})
        response = requests.get('http://www.youtube.com/results?search_query=' + search_string)
        if response.status_code == 200:
            search_results = re.findall('href=\\"\\/watch\\?v=(.{11})', response.content.decode())
            first_result_url = 'http://www.youtube.com/watch?v=' + search_results[0]
            await ctx.send(first_result_url)
            self.logger.info(misolog.format_log(ctx, f"{first_result_url}"))
        else:
            await ctx.send("Error: status code " + str(response.status_code))
            self.logger.info(misolog.format_log(ctx, f"error{response.status_code}"))

    @commands.command(name='wikipedia')
    async def wikipedia(self, ctx, *args):
        """Search wikipedia for the given search query"""
        if args[0] == 'random':
            search_string = wp.random()
        else:
            search_string = ' '.join(args)
        try:
            page = wp.page(search_string)
            await ctx.send(page.url)
            self.logger.info(misolog.format_log(ctx, f""))
        except wp.exceptions.DisambiguationError as error:
            await ctx.send(f"```{str(error)}```")
            self.logger.info(misolog.format_log(ctx, f"Disambiguation page"))

    @commands.command(name='navyseal')
    async def navyseal(self, ctx):
        """Navy seal copypasta"""
        self.logger.info(misolog.format_log(ctx, f""))
        copypasta = data_json['strings']['navyseal_copypasta']
        await ctx.send(copypasta)

    @commands.command(name='stan', aliases=['Stan'])
    async def stan(self, ctx, *args):
        """Gets a random kpop artist from a list scraped from kprofiles.com"""
        if args:
            if args[0] == 'update':
                amount = len(self.artists)
                self.artists = []
                urls_to_scrape = ['https://kprofiles.com/k-pop-girl-groups/',
                                  'https://kprofiles.com/k-pop-boy-groups/',
                                  'https://kprofiles.com/co-ed-groups-profiles/',
                                  'https://kprofiles.com/kpop-duets-profiles/',
                                  'https://kprofiles.com/kpop-solo-singers/']
                for url in urls_to_scrape:
                    self.artists += scrape_kprofiles(url)

                data_json['artists'] = self.artists
                save_data()

                await ctx.send(f"Artist list succesfully updated, {len(self.artists) - amount} new entries, "
                               f"{len(self.artists)} total entries")
                self.logger.info(misolog.format_log(ctx, f"artist list updated; {len(self.artists) - amount} new, "
                                                         f"{len(self.artists)} total"))
                return

            elif args[0] == 'clear':
                self.artists = []
                data_json['artists'] = self.artists
                save_data()
                self.logger.info(misolog.format_log(ctx, f"artist list cleared"))
                return
        try:
            artist = str(rd.choice(self.artists))
            await ctx.send('stan ' + artist)
            self.logger.info(misolog.format_log(ctx, f"artist={artist}"))
        except IndexError as e:
            print(f"{ctx.message.author} >stan: " + str(e))
            await ctx.send("Error: artist list is empty, please use >stan update")
            self.logger.warning(misolog.format_log(ctx, f"artist list empty"))

    @commands.command()
    async def ascii(self, ctx, *args):
        self.logger.info(misolog.format_log(ctx, f""))
        text = " ".join(args)
        response = requests.get(f"https://artii.herokuapp.com/make?text={text}")
        content = f"```{response.content.decode('utf-8')}```"
        await ctx.send(content)

    @commands.command()
    async def igvideo(self, ctx, url):
        """Get the source video from an instagram post"""
        response = requests.get(url, headers={"Accept-Encoding": "utf-8"})
        tree = html.fromstring(response.content)
        results = tree.xpath('//meta[@content]')
        contents = []
        for result in results:
            contents.append(result.attrib['content'])
        sources = []
        for content in contents:
            if content.endswith(".mp4"):
                sources.append(content)
        if sources:
            await ctx.send(sources[0])
            self.logger.info(misolog.format_log(ctx, f"Success"))
        else:
            await ctx.send("Found nothing, sorry!")
            self.logger.warning(misolog.format_log(ctx, f"Found nothing"))

    @commands.command()
    async def ig(self, ctx, url):
        """Get the source images from an instagram post"""
        response = requests.get(url, headers={"Accept-Encoding": "utf-8"})
        soup = BeautifulSoup(response.text, 'html.parser')
        script = soup.find_all('script')
        sources = []
        for i in range(len(script)):
            urls = re.findall('"display_url":"(.*?)"', script[i].text)
            if urls:
                sources = urls
        sources = list(set(sources))

        if sources:
            content = ""
            for url in sources:
                content += f"{url}\n"
            await ctx.send(content)
            self.logger.info(misolog.format_log(ctx, f"Success"))
        else:
            await ctx.send("Found nothing, sorry!")
            self.logger.warning(misolog.format_log(ctx, f"Found nothing"))

    @commands.command(name="ytmp3")
    async def ytmp3(self, ctx, url):
        async with ctx.typing():
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title)s.mp3',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192'
                }]
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                title = ydl.extract_info(url=url).get('title', None).replace('"', "'")

            with open(f"downloads/{title}.mp3", "rb") as f:
                await ctx.send(file=discord.File(f))
                self.logger.info(misolog.format_log(ctx, f""))
            try:
                os.remove(f"downloads/{title}.mp3")
            except OSError as e:
                self.logger.warning(f"Failed to delete {title}.mp3")
                print(str(e))

    @commands.command()
    async def question(self, ctx, *args):
        if args:
            choices = ["Yes, definitely.", "Yes.", "I think so, yes.", "Maybe.", "No.", "Most likely not.", "Definitely not."]
            answer = rd.choice(choices)
            await ctx.send(f"**{answer}**")
        else:
            await ctx.send("You must ask something to receive an answer!")

    @commands.command()
    async def choose(self, ctx, *args):
        query = " ".join(args)
        choices = query.split(" or ")
        await ctx.send(f"I choose **{rd.choice(choices).strip()}**")


def scrape_kprofiles(url):
    """Scrape the given kprofiles url for artist names and return the results"""
    page = requests.get(url)
    tree = html.fromstring(page.content)
    results = tree.xpath('//article/div/div/div/p/a[@href]/text()')
    filtered_results = []
    discarded_results = 0
    for item in results:
        if item in ["\n", " ", ""]:
            discarded_results += 1
            continue
        else:
            if "Profile" in item:
                item = item.replace("Profile", "")
            filtered_results.append(item.strip())
    print(f"discarded {discarded_results} results in {url}")
    return filtered_results


def setup(client):
    client.add_cog(Commands(client))
