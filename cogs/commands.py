from __future__ import unicode_literals
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
import os
import main
import psutil
import math
import json
import asyncio
import datetime
from utils import minestat


database = main.database


class Commands:

    def __init__(self, client):
        self.client = client
        self.start_time = time.time()
        self.artists = database.get_attr("data", "artists")
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
        content.title = "Patreon supporters ❤"
        content.description = "\n".join([self.client.get_user(x).mention for x in patrons])
        await ctx.send(embed=content)

    @commands.command(name='info')
    async def info(self, ctx):
        """Get information about the bot"""
        self.logger.info(misolog.format_log(ctx, f""))
        appinfo = await self.client.application_info()
        info_embed = discord.Embed(title='Hello',
                                   description=f'I am Miso Bot, created by {appinfo.owner.mention}.\n'
                                   'See the documentation website for a list of commands, '
                                   'or use the `>help` command.'
                                               f'\n\nCurrently active in {len(self.client.guilds)} servers.',
                                   colour=discord.Colour.magenta())

        info_embed.set_footer(text=f'version {main.version}')
        info_embed.set_thumbnail(url=self.client.user.avatar_url)
        info_embed.add_field(name='Github', value='https://github.com/joinemm/Miso-Bot', inline=False)
        info_embed.add_field(name='Documentation', value="http://joinemm.me/misobot", inline=False)
        info_embed.add_field(name='Patreon', value="https://www.patreon.com/joinemm", inline=False)

        await ctx.send(embed=info_embed)

    @commands.command(name='ping')
    async def ping(self, ctx):
        """Get the bot's ping"""
        pong_msg = await ctx.send(":ping_pong:")
        sr_lat = (pong_msg.created_at - ctx.message.created_at).total_seconds() * 1000
        await pong_msg.edit(content=f"```latency = {sr_lat}ms\n"
                                    f"heartbeat = {self.client.latency*1000:.1f}ms```")
        self.logger.info(misolog.format_log(ctx, f""))

    @commands.command(name="status", aliases=["uptime"])
    async def status(self, ctx):
        """Get the bot's status"""
        self.logger.info(misolog.format_log(ctx, f""))
        up_time = time.time() - self.start_time
        m, s = divmod(up_time, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        uptime_string = "%d days %d hours %d minutes %d seconds" % (d, h, m, s)

        stime = time.time() - psutil.boot_time()
        m, s = divmod(stime, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        system_uptime_string = "%d days %d hours %d minutes %d seconds" % (d, h, m, s)

        mem = psutil.virtual_memory()

        pid = os.getpid()
        memory_use = psutil.Process(pid).memory_info()[0]

        content = discord.Embed(title=f"Miso Bot | version {main.version}")
        content.set_thumbnail(url=self.client.user.avatar_url)

        content.add_field(name="Bot process uptime", value=uptime_string)
        content.add_field(name="System CPU Usage", value=f"{psutil.cpu_percent()}%")
        content.add_field(name="System uptime", value=system_uptime_string)

        content.add_field(name="System RAM Usage", value=f"{mem.percent}%")
        content.add_field(name="Bot memory usage", value=f"{memory_use/math.pow(1024, 2):.2f}MB")

        await ctx.send(embed=content)

    @commands.command(name='random')
    async def rng(self, ctx, _range=1):
        """Gives random integer from 0 to given input"""
        content = rd.randint(0, int(_range))
        await ctx.send(content)
        self.logger.info(misolog.format_log(ctx, f"range=[0,{_range}], result={content}"))

    @commands.command(name='youtube', aliases=["yt"])
    async def youtube(self, ctx, *args):
        """Search youtube for the given search query and return first result"""
        if not args:
            await ctx.send("usage: `>youtube [search string]`")
            return
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
        copypasta = database.get_attr("data", "strings.navyseal_copypasta")
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

                database.set_attr("data", "artists", self.artists)

                await ctx.send(f"Artist list succesfully updated, {len(self.artists) - amount} new entries, "
                               f"{len(self.artists)} total entries")
                self.logger.info(misolog.format_log(ctx, f"artist list updated; {len(self.artists) - amount} new, "
                                                         f"{len(self.artists)} total"))
                return

            elif args[0] == 'clear':
                self.artists = []
                database.set_attr("data", "artists", self.artists)
                await ctx.send("Artist list cleared")
                self.logger.info(misolog.format_log(ctx, f"artist list cleared"))
                return

        if self.artists:
            artist = str(rd.choice(self.artists))
            await ctx.send('stan ' + artist)
            self.logger.info(misolog.format_log(ctx, f"artist={artist}"))
        else:
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
        found_date = False
        post_date = None
        for i in range(len(script)):
            urls = re.findall('"display_url":"(.*?)"', script[i].text)
            if urls:
                sources = urls
            if not found_date:
                try:
                    data = json.loads(script[i].text, encoding='utf-8')
                    datestring = data.get('uploadDate')
                    post_date = datetime.datetime.strptime(datestring, "%Y-%m-%dT%H:%M:%S")
                    found_date = True
                except json.JSONDecodeError:
                    pass
        sources = list(set(sources))

        date = re.findall('<script type="application/ld+json">(.*?)</script>', response.text)
        print(date)

        if sources:
            content = discord.Embed(title=soup.title.string, url=url)
            if post_date is not None:
                content.timestamp = post_date
            for url in sources:
                content.set_image(url=url)
                await ctx.send(embed=content)
            self.logger.info(misolog.format_log(ctx, f"Success"))
        else:
            await ctx.send("Found nothing, sorry!")
            self.logger.warning(misolog.format_log(ctx, f"Found nothing"))

    @commands.command(aliases=["gif", "gfy"])
    async def gfycat(self, ctx, *args):
        """Search for a random gif"""
        self.logger.info(misolog.format_log(ctx, f""))
        if not args:
            await ctx.send("Give me something to search!")
            return

        query = ' '.join(args)
        scripts = []
        if len(args) == 1:
            url = f"https://gfycat.com/gifs/tag/{query}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            scripts += soup.find_all('script')

        url = f"https://gfycat.com/gifs/search/{query}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts += soup.find_all('script')
        urls = []
        for i in range(len(scripts)):
            try:
                data = json.loads(scripts[i].text, encoding='utf-8')
                for x in data["itemListElement"]:
                    if "url" in x:
                        urls.append(x['url'])
            except json.JSONDecodeError:
                pass

        if not urls:
            await ctx.send("Found nothing!")
            return

        # print(f"found {len(urls)} gifs")
        msg = await ctx.send(f"**{query}**: {rd.choice(urls)}")
        await msg.add_reaction("❌")

        def check(_reaction, _user):
            return _reaction.message.id == msg.id and _reaction.emoji == "❌" and _user == ctx.author

        try:
            await self.client.wait_for('reaction_add', timeout=120.0, check=check)
        except asyncio.TimeoutError:
            return
        else:
            await msg.delete()

    @commands.command(name="8ball")
    async def eightball(self, ctx, *args):
        """Ask a yes/no question"""
        if args:
            choices = ["Yes, definitely.", "Yes.", "Most likely yes.", "I think so, yes.",
                       "Absolutely, no question about it", "Maybe.", "Perhaps.", "It's possible, but not likely."
                                                                                 "I don't think so.", "No.",
                       "Most likely not.", "Definitely not.", "No way."]
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

    @commands.command()
    async def pewdiepie(self, ctx):
        """Pewdiepie VS T-series"""
        self.logger.info(misolog.format_log(ctx, f""))
        pewdiepie = get_subcount("pewdiepie")
        tseries = get_subcount("tseries")

        content = discord.Embed(color=discord.Color.magenta(), title="Pewdiepie VS T-Series live subscriber count:",
                                url="https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw?sub_confirmation=1")
        content.add_field(name="Pewdiepie", value="**{:,}**".format(pewdiepie))
        content.add_field(name="T-Series", value="**{:,}**".format(tseries))
        if pewdiepie >= tseries:
            desc = "PewDiePie is currently {:,} subscribers ahead of T-Series!".format(pewdiepie-tseries)
            content.set_thumbnail(
                url="https://yt3.ggpht.com/a-/AAuE7mAPBVgUYqlLw9SvJyKAVWmgkQ2-KrkgSv4_5A=s288-mo-c-c0xffffffff-rj-k-no")
        else:
            desc = "T-Series is currently {:,} subscribers ahead of PewDiePie!".format(tseries-pewdiepie)
            content.set_thumbnail(
                url="https://yt3.ggpht.com/a-/AAuE7mBlVCRJawuU4QYf21y-Fx-cc8c9HhExSiAPtQ=s288-mo-c-c0xffffffff-rj-k-no")
        # content.timestamp = ctx.message.created_at
        content.set_footer(text=desc)
        await ctx.send(embed=content)

    @commands.command()
    async def minecraft(self, ctx, address="mc.joinemm.me"):
        """Get the status of a minecraft server"""
        server = minestat.MineStat(address, 25565)
        content = discord.Embed()
        # content.title = f"`{server.address} : {server.port}`"
        content.colour = discord.Color.green()
        if server.online:
            content.add_field(name="Server Address", value=f"`{server.address}`")
            content.add_field(name="Version", value=server.version)
            content.add_field(name="Players", value=f"{server.current_players}/{server.max_players}")
            content.add_field(name="Latency", value=f"{server.latency}ms")
            content.set_footer(text=f"{server.motd}")
        else:
            content.description = "**Server is offline**"
        content.set_thumbnail(url="https://vignette.wikia.nocookie.net/potcoplayers/images/c/c2/"
                                  "Minecraft-icon-file-gzpvzfll.png/revision/latest?cb=20140813205910")
        await ctx.send(embed=content)


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
    return filtered_results


def get_subcount(username):
    urls = {"pewdiepie": "https://bastet.socialblade.com/youtube/lookup?query=UC-lHJZR3Gqxm24_Vd_AJ5Yw",
            "tseries": "https://bastet.socialblade.com/youtube/lookup?query=UCq-Fj5jknLsUf-MWSy4_brA"}
    url = urls.get(username)
    if url is None:
        return None
    while True:
        try:
            response = requests.get(url=url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0",
                "Origin": "https://socialblade.com",
                "Host": "bastet.socialblade.com"}, timeout=1)
        except requests.exceptions.ReadTimeout:
            continue
        if response.status_code == 200:
            try:
                subcount = int(response.content.decode('utf-8'))
                break
            except ValueError:
                continue

    return subcount


def setup(client):
    client.add_cog(Commands(client))
