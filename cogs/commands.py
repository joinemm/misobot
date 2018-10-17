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

with open('dont commit\keys.txt', 'r') as filehandle:
    keys = json.load(filehandle)
    WEATHER_TOKEN = keys['WEATHER_API']
    OXFORD_APPID = keys['OXFORD_APPID']
    OXFORD_TOKEN = keys['OXFORD_TOKEN']
    NAVER_APPID = keys['NAVER_APPID']
    NAVER_TOKEN = keys['NAVER_TOKEN']

with open('data.json', 'r') as filehandle:
    data = json.load(filehandle)
    print('data.json loaded succesfully')


class Commands:

    def __init__(self, client):
        self.client = client
        self.artists = data

    @commands.command(name='info', brief='Get information about the bot')
    async def info(self, ctx):
        info_embed = discord.Embed(title='Hello',
                                   description='I am Miso Bot, created by Joinemm. Use >help for a list of commands',
                                   colour=discord.Colour.magenta())

        info_embed.set_footer(text='version 0.04')
        info_embed.set_thumbnail(url=self.client.user.avatar_url)
        info_embed.add_field(name='Github', value='https://github.com/joinemm/Miso-Bot', inline=False)

        await ctx.send(embed=info_embed)

    @commands.command(name='ping', brief="Gets the bot's ping")
    async def ping(self, ctx):
        pong_msg = await ctx.send(":ping_pong:")
        ms = (pong_msg.created_at - ctx.message.created_at).total_seconds() * 1000
        await pong_msg.edit(content=f":ping_pong: {ms}ms")

    """
    @commands.command(name='say', brief='Makes the bot say what you want')
    async def say(self, ctx, *args):
        content = ""
        for word in args:
            content += word + " "
        await ctx.send(content)
        await ctx.message.delete()
    """

    @commands.command(name='random', brief='Gives random integer from range 0-{input}')
    async def random(self, ctx, cap=1):
        content = rd.randint(0, int(cap))
        await ctx.send(content)

    @commands.command(name='youtube', brief='Searches the given video from youtube')
    async def youtube(self, ctx, *args):
        search_string = ''
        for word in args:
            search_string += word + ' '
        query_string = urllib.parse.urlencode({'search_query': search_string})
        html_content = urllib.request.urlopen('http://www.youtube.com/results?' + query_string)
        search_results = re.findall('href=\\"\\/watch\\?v=(.{11})', html_content.read().decode())
        result = 'http://www.youtube.com/watch?v=' + search_results[0]
        await ctx.send(result)

    @commands.command(name='wikipedia', brief='Searches the given page from wikipedia')
    async def wikipedia(self, ctx, *args):
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

    @commands.command(name='navyseal')
    async def navyseal(self, ctx):
        copypasta = "What the fuck did you just fucking say about me, you little bitch? I'll have you know I graduated top of my class in the Navy Seals, and I've been involved in numerous secret raids on Al-Quaeda, and I have over 300 confirmed kills. I am trained in gorilla warfare and I'm the top sniper in the entire US armed forces. You are nothing to me but just another target. I will wipe you the fuck out with precision the likes of which has never been seen before on this Earth, mark my fucking words. You think you can get away with saying that shit to me over the Internet? Think again, fucker. As we speak I am contacting my secret network of spies across the USA and your IP is being traced right now so you better prepare for the storm, maggot. The storm that wipes out the pathetic little thing you call your life. You're fucking dead, kid. I can be anywhere, anytime, and I can kill you in over seven hundred ways, and that's just with my bare hands. Not only am I extensively trained in unarmed combat, but I have access to the entire arsenal of the United States Marine Corps and I will use it to its full extent to wipe your miserable ass off the face of the continent, you little shit. If only you could have known what unholy retribution your little clever comment was about to bring down upon you, maybe you would have held your fucking tongue. But you couldn't, you didn't, and now you're paying the price, you goddamn idiot. I will shit fury all over you and you will drown in it. You're fucking dead, kiddo."
        await ctx.send(copypasta)

    @commands.command(name='stan', brief='Gives you a random korean artist to stan')
    async def stan(self, ctx, *args):
        if args:
            if args[0] == 'update':
                amount = len(self.artists)

                print(f'''Updating artists.txt... current amount of artists is {amount}''')

                self.artists = []
                urls_to_scrape = ['https://kprofiles.com/k-pop-girl-groups/', 'https://kprofiles.com/k-pop-boy-groups/',
                                  'https://kprofiles.com/co-ed-groups-profiles/',
                                  'https://kprofiles.com/kpop-duets-profiles/',
                                  'https://kprofiles.com/kpop-solo-singers/']
                for url in urls_to_scrape:
                    self.artists += scrape_kprofiles(url)

                print(f'''Artist list updated. new amount of artists is {len(self.artists)}''')

                with open('artists.txt', 'w') as filehandle:
                    json.dump(self.artists, filehandle)
                    print('New artists succesfully dumped to artists.txt')
                    await ctx.send(
                        f"Artist list succesfully updated, {len(self.artists) - amount} new entries, "
                        f"{len(self.artists)} total entries")
                return

            elif args[0] == 'clear':
                print('Clearing artist list...')
                self.artists = []
                with open('artists.txt', 'w') as filehandle:
                    json.dump(self.artists, filehandle)
                    print('Artist list cleared')
                    await ctx.send('Artist list succesfully cleared')
                return

        try:
            artist = str(rd.choice(self.artists))
            await ctx.send('stan ' + artist)
            print(f'''selected {artist} out of {len(self.artists)} artists''')
        except IndexError:
            error = 'Error: artist list is empty, please use >stan update'
            print(error)
            await ctx.send(error)

    @commands.command(name='weather', brief='Gets the weather of a given city')
    async def weather(self, ctx, *args):
        try:
            city = ' '.join(args)
            response = requests.get(
                f'''http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_TOKEN}''')
            weather_data = json.loads(response.content.decode('utf-8'))
            weather = weather_data['weather'][0]['main']
            await ctx.send(f'''Weather in {city}: {weather}''')
        except Exception as error:
            await ctx.send(f'''Error: {error}''')

    @commands.command(name='define', brief='Searches the given word from oxford dictionary')
    async def define(self, ctx, *args):
        search_string = ' '.join(args).lower()
        api_url = 'https://od-api.oxforddictionaries.com:443/api/v1'
        print('searching with query ' + search_string)
        query = f'''/search/en?q={search_string}&prefix=false'''
        id_response = requests.get(api_url + query, headers={
            'Accept': 'application/json',
            'app_id': OXFORD_APPID,
            'app_key': OXFORD_TOKEN,
        })
        rescode = id_response.status_code
        if rescode == 200:
            json_data = json.loads(id_response.content.decode('utf-8'))
            try:
                word_id = json_data['results'][0]['id']
                word_string = json_data['results'][0]['word']
                print(('found ' + word_id) + ' as word_id')
                response = requests.get((api_url + '/entries/en/') + word_id, headers={
                    'Accept': 'application/json',
                    'app_id': OXFORD_APPID,
                    'app_key': OXFORD_TOKEN,
                })
                json_data = json.loads(response.content.decode('utf-8'))
                all_entries = []
                for entry in json_data['results'][0]['lexicalEntries']:
                    name = json_data['results'][0]['word']
                    definition = entry['entries'][0]['senses'][0]['definitions'][0]
                    word_type = entry['lexicalCategory']
                    this_entry = {"id": name, "definition": definition, "type": word_type}
                    all_entries.append(this_entry)

                definitions_embed = discord.Embed(colour=discord.Colour.blue())
                definitions_embed.set_author(name=word_string.capitalize(), icon_url="https://i.imgur.com/vDvSmF3.png")

                for entry in all_entries:
                    definitions_embed.add_field(name=entry["type"], value=entry["definition"].capitalize(), inline=False)

                await ctx.send(embed=definitions_embed)
            except Exception as e:
                print(e)
                await ctx.send('Error: no definition found for ' + search_string)
        else:
            await ctx.send('Error: status code' + str(id_response.status_code))

    @commands.command(name='translate', brief='Translates given text from KR/JP -> EN or EN -> KR')
    async def translate(self, ctx, *args):
        search_string = urllib.parse.quote(' '.join(args))
        detected_lang = detect_language(search_string)
        if detected_lang == 'ko':
            source_lang = 'ko'
            target_lang = 'en'
        elif detected_lang == 'ja':
            source_lang = 'ja'
            target_lang = 'en'
        else:
            source_lang = 'en'
            target_lang = 'ko'
        query = f'''source={source_lang}&target={target_lang}&text={search_string}'''
        print(query)
        api_url = 'https://openapi.naver.com/v1/papago/n2mt'
        request = urllib.request.Request(api_url)
        request.add_header('X-Naver-Client-Id', NAVER_APPID)
        request.add_header('X-Naver-Client-Secret', NAVER_TOKEN)
        response = urllib.request.urlopen(request, data=query.encode('utf-8'))
        rescode = response.getcode()
        if rescode == 200:
            response_body = json.loads(response.read().decode('utf-8'))
            print(response_body)
            translation = response_body['message']['result']['translatedText']
            await ctx.send(translation)
        else:
            print('Error Code:' + str(rescode))
            print(response)


def scrape_kprofiles(url):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    results = tree.xpath('//article/div/div/div/p/a[@href]/text()')
    filtered_results = []
    discarded_results = 0
    for item in results:
        if item in ['\n', ' ']:
            discarded_results += 1
            continue
        else:
            if 'Profile' in item:
                item = item.replace('Profile', '')
            filtered_results.append(item.strip())
    print(f'''discarded {discarded_results} results''')
    return filtered_results


def detect_language(string):
    api_url = 'https://openapi.naver.com/v1/papago/detectLangs'
    query = 'query=' + string
    request = urllib.request.Request(api_url)
    request.add_header('X-Naver-Client-Id', NAVER_APPID)
    request.add_header('X-Naver-Client-Secret', NAVER_TOKEN)
    response = urllib.request.urlopen(request, data=query.encode('utf-8'))
    rescode = response.getcode()
    if rescode == 200:
        response_body = json.loads(response.read().decode('utf-8'))
        print(response_body)
        return response_body['langCode']
    else:
        print('Error Code (detect_language):' + str(rescode))
        return None


def setup(client):
    client.add_cog(Commands(client))
