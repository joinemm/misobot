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
import datetime


def load_data():
    with open('data/data.json', 'r') as filehandle:
        data = json.load(filehandle)
        return data


def save_data():
    with open('data/data.json', 'w') as filehandle:
        json.dump(data_json, filehandle, indent=4)


data_json = load_data()


class Commands:

    def __init__(self, client):
        self.client = client
        self.start_time = time.time()
        self.artists = data_json['artists']
        self.logger = misolog.create_logger(__name__)

    @commands.command()
    async def patreon(self, ctx):
        """Link to the patreon page"""
        await ctx.send("https://www.patreon.com/joinemm")

    @commands.command()
    async def patrons(self, ctx):
        """List the current patreons"""
        patrons = [381491116853166080, 121757433507872768]
        content = discord.Embed()
        content.title = "Current Patrons:"
        content.description = "\n".join([self.client.get_user(x).mention for x in patrons])
        await ctx.send(embed=content)

    @commands.command(name='info')
    async def info(self, ctx):
        """Get information about the bot"""
        self.logger.info(misolog.format_log(ctx, f""))
        appinfo = await self.client.application_info()
        info_embed = discord.Embed(title='Hello',
                                   description=f'I am Miso Bot, created by {appinfo.owner.mention}.\n'
                                               'See the documentation website for a list of commands.'
                                               f'\n\nCurrently active in {len(self.client.guilds)} servers.',
                                   colour=discord.Colour.magenta())

        info_embed.set_footer(text='version 1.0.0')
        info_embed.set_thumbnail(url=self.client.user.avatar_url)
        info_embed.add_field(name='Github', value='https://github.com/joinemm/Miso-Bot', inline=False)
        info_embed.add_field(name='Documentation', value="http://joinemm.me/misobot", inline=False)
        info_embed.add_field(name='Patreon', value="https://www.patreon.com/joinemm", inline=False)

        await ctx.send(embed=info_embed)

    @commands.command(name='ping')
    async def ping(self, ctx):
        """Get the bot's ping"""
        #time_beg = datetime.datetime.utcnow()
        pong_msg = await ctx.send(":ping_pong:")
        #time_sent = datetime.datetime.utcnow()
        sr_lat = (pong_msg.created_at - ctx.message.created_at).total_seconds() * 1000
        #re_lat = (time_beg-ctx.message.created_at).total_seconds() * 1000
        #se_lat = (time_sent-time_beg).total_seconds() * 1000
        await pong_msg.edit(content=f"```latency = {sr_lat}ms\n"
                                    f"heartbeat = {self.client.latency*1000:.1f}ms```")
        self.logger.info(misolog.format_log(ctx, f""))

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

    @commands.command(name='youtube', aliases=["yt"])
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
        """Turn text into fancy ascii art"""
        self.logger.info(misolog.format_log(ctx, f""))
        text = " ".join(args)
        response = requests.get(f"https://artii.herokuapp.com/make?text={text}")
        content = f"```{response.content.decode('utf-8')}```"
        await ctx.send(content)

    @commands.command()
    async def igvideo(self, ctx, url):
        """Get the source video from an instagram post"""
        response = requests.get(url.replace("`", ""), headers={"Accept-Encoding": "utf-8"})
        tree = html.fromstring(response.content)
        results = tree.xpath('//meta[@content]')
        sources = []
        for result in results:
            try:
                if result.attrib['property'] == "og:video":
                    sources.append(result.attrib['content'])
            except KeyError:
                pass
        if sources:
            await ctx.send(sources[0])
            self.logger.info(misolog.format_log(ctx, f"Success"))
        else:
            await ctx.send("Found nothing, sorry!")
            self.logger.warning(misolog.format_log(ctx, f"Found nothing"))

    @commands.command()
    async def ig(self, ctx, url):
        """Get the source images from an instagram post"""
        response = requests.get(url.replace("`", ""), headers={"Accept-Encoding": "utf-8"})
        soup = BeautifulSoup(response.text, 'html.parser')
        script = soup.find_all('script')
        sources = []
        for i in range(len(script)):
            urls = re.findall('"display_url":"(.*?)"', script[i].text)
            if urls:
                sources = urls
        sources = list(set(sources))

        if sources:
            content = discord.Embed()
            for url in sources:
                content.set_image(url=url)
                await ctx.send(embed=content)
            self.logger.info(misolog.format_log(ctx, f"Success"))
        else:
            await ctx.send("Found nothing, sorry!")
            self.logger.warning(misolog.format_log(ctx, f"Found nothing"))

    @commands.command(name="ytmp3")
    async def ytmp3(self, ctx, url):
        """Turn youtube video into downloadable mp3 file"""
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

    @commands.command(name="8ball")
    async def eightball(self, ctx, *args):
        """Ask a yes/no question"""
        if args:
            choices = ["Yes, definitely.", "Yes.", "I think so, yes.", "Maybe.", "No.", "Most likely not.", "Definitely not."]
            answer = rd.choice(choices)
            await ctx.send(f"**{answer}**")
            self.logger.info(misolog.format_log(ctx, f"{answer}"))
        else:
            await ctx.send("You must ask something to receive an answer!")
            self.logger.warning(misolog.format_log(ctx, f"question=None"))

    @commands.command()
    async def choose(self, ctx, *args):
        """Choose from given options. split options with 'or'"""
        query = " ".join(args)
        choices = query.split(" or ")
        if len(choices) < 2:
            await ctx.send("Give me at least 2 options to choose from! (separate options with `or`)")
            self.logger.warning(misolog.format_log(ctx, f"1 option"))
            return
        choice = rd.choice(choices).strip()
        await ctx.send(f"I choose **{choice}**")
        self.logger.info(misolog.format_log(ctx, f"{choice}"))

    @commands.command()
    async def melon(self, ctx, timeframe="", amount=10):
        """Get realtime / daily / monthly chart from Melon"""
        self.logger.info(misolog.format_log(ctx, f""))
        if timeframe not in ["day", "month", "rise", ""]:
            if timeframe == "realtime":
                timeframe = ""
            else:
                await ctx.send(f"ERROR: Invalid timeframe `{timeframe}`\ntry `[realtime | day | month | rise]`")
                return
        if amount > 100:
            amount = 100
        url = f"https://www.melon.com/chart/{timeframe}/index.htm"

        source = requests.get(url, headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0"})
        tree = html.fromstring(source.content)

        song_titles = tree.xpath('//div[@class="ellipsis rank01"]/span/a/text()')
        artists = tree.xpath('//div[@class="ellipsis rank02"]/a/text()')
        albums = tree.xpath('//div[@class="ellipsis rank03"]/a/text()')
        image = tree.xpath('//img[@onerror="WEBPOCIMG.defaultAlbumImg(this);"]')[0].attrib['src']

        content = discord.Embed(title=f"Melon top {amount} - {timeframe}", colour=discord.Colour.green())
        content.set_thumbnail(url=image)
        for i in range(amount):
            content.add_field(name=f"{i + 1}. {song_titles[i]}", value=f"{artists[i]} - {albums[i]}", inline=False)

        await ctx.send(embed=content)

    @commands.command()
    async def ship(self, ctx, *args):
        """Ship two people, separate names with 'and'"""
        names = " ".join(args).split("and")
        if not len(names) == 2:
            await ctx.send("Please give two names separated with `and`")
            return
        url = f"https://www.calculator.net/love-calculator.html?cnameone={names[0]}&x=0&y=0&cnametwo={names[1]}"
        source = requests.get(url)
        tree = html.fromstring(source.content)
        percentage = tree.xpath('//font[@color="green"]/b/text()')[0]
        text = tree.xpath('//div[@id="content"]/p/text()')

        perc = int(percentage[:-1])
        if perc < 26:
            emoji = ":broken_heart:"
        elif perc > 74:
            emoji = ":sparkling_heart:"
        else:
            emoji = ":hearts:"
        content = discord.Embed(title=f"{names[0]} {emoji} {names[1]} - {percentage}", colour=discord.Colour.magenta())
        content.description = text[2]

        await ctx.send(embed=content)
        self.logger.info(misolog.format_log(ctx, f"{percentage}"))

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
