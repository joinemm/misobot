import json
import random as rd
import re
import discord
import requests
import wikipedia as wp
from discord.ext import commands
from lxml import html


def load_data():
    with open('data.json', 'r') as filehandle:
        data = json.load(filehandle)
        print('data.json loaded')
        return data


def save_data():
    with open('data.json', 'w') as filehandle:
        json.dump(data_json, filehandle, indent=4)
        print('data.json saved')


data_json = load_data()


class Commands:

    def __init__(self, client):
        self.client = client
        self.artists = data_json['artists']

    @commands.command(name='info', brief='Get information about the bot')
    async def info(self, ctx):
        print(f"{ctx.message.author} >info")
        info_embed = discord.Embed(title='Hello',
                                   description='I am Miso Bot, created by Joinemm. Use >help for a list of commands.'
                                               f'\n\nCurrently active in {len(self.client.guilds)} servers.',
                                   colour=discord.Colour.magenta())

        info_embed.set_footer(text='version 0.1.3')
        info_embed.set_thumbnail(url=self.client.user.avatar_url)
        info_embed.add_field(name='Github', value='https://github.com/joinemm/Miso-Bot', inline=False)

        await ctx.send(embed=info_embed)

    @commands.command(name='ping', brief="Get the bot's ping")
    async def ping(self, ctx):
        print(f"{ctx.message.author} >ping")
        pong_msg = await ctx.send(":ping_pong:")
        ms = (pong_msg.created_at - ctx.message.created_at).total_seconds() * 1000
        await pong_msg.edit(content=f":ping_pong: {ms}ms")

    @commands.command(name='random', brief='Gives random integer from range 0-{input}')
    async def random(self, ctx, cap=1):
        print(f"{ctx.message.author} >random")
        content = rd.randint(0, int(cap))
        await ctx.send(content)

    @commands.command(name='youtube', brief='Search a video from youtube')
    async def youtube(self, ctx, *args):
        print(f"{ctx.message.author} >youtube {args}")
        search_string = " ".join(args)
        response = requests.get('http://www.youtube.com/results?search_query=' + search_string)
        if response.status_code == 200:
            search_results = re.findall('href=\\"\\/watch\\?v=(.{11})', response.content.decode())
            first_result_url = 'http://www.youtube.com/watch?v=' + search_results[0]
            await ctx.send(first_result_url)
        else:
            await ctx.send("Error: status code " + str(response.status_code))

    @commands.command(name='wikipedia', brief='Search from wikipedia')
    async def wikipedia(self, ctx, *args):
        print(f"{ctx.message.author} >wikipedia {args}")
        if args[0] == 'random':
            search_string = wp.random()
        else:
            search_string = ' '.join(args)
        try:
            page = wp.page(search_string)
            await ctx.send(page.url)
        except wp.exceptions.DisambiguationError as error:
            print(error)
            await ctx.send(('```' + str(error)) + '```')

    @commands.command(name='navyseal',brief='What the fuck did you just-')
    async def navyseal(self, ctx):
        print(f"{ctx.message.author} >navyseal")
        copypasta = data_json['strings']['navyseal_copypasta']
        await ctx.send(copypasta)

    @commands.command(name='stan', brief='Get a random korean artist to stan', aliases=['Stan'])
    async def stan(self, ctx, *args):
        print(f"{ctx.message.author} >stan {args}")
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

                print(f"Artist list succesfully updated, {len(self.artists) - amount} new entries, "
                      f"{len(self.artists)} total entries")

                data_json['artists'] = self.artists
                save_data()

                await ctx.send(f"Artist list succesfully updated, {len(self.artists) - amount} new entries, "
                               f"{len(self.artists)} total entries")
                return

            elif args[0] == 'clear':
                print('Clearing artist list...')
                self.artists = []
                data_json['artists'] = self.artists
                save_data()
                return
            else:
                print(f'invalid argument {args}')
        try:
            artist = str(rd.choice(self.artists))
            await ctx.send('stan ' + artist)
            print(f"{ctx.message.author} >stan: {artist}")
        except IndexError as e:
            print(f"{ctx.message.author} >stan: " + str(e))
            await ctx.send("Error: artist list is empty, please use >stan update")


def scrape_kprofiles(url):
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
