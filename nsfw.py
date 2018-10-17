import discord
from discord.ext import commands
from discord.http import Route
import requests
from lxml import html


class Nsfw:

    def __init__(self, client):
        self.client = client
        scrape_ph('string')

    @commands.command()
    async def nsfw(self, ctx):
        channel_nsfw = ctx.channel.is_nsfw()
        if channel_nsfw:
            print('nsfw')
            await ctx.send("current channel is nsfw")
        else:
            print('nope')
            await ctx.send("current channel is NOT nsfw")


def scrape_ph(string):
    url = 'https://www.pornhub.com/video/search?search=' + string
    page = requests.get(url)
    tree = html.fromstring(page.content)
    results = tree.xpath('//ul[@id="videoSearchResult"]/li[@class="js-pop videoblock videoBox"]')
    vkeys = []
    for result in results:
        vkeys.append(result.attrib['_vkey'])
    return vkeys


def setup(client):
    client.add_cog(Nsfw(client))
