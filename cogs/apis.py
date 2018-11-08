import json
import urllib.parse
import urllib.request
import discord
import requests
from discord.ext import commands
import spotipy.util as util
import spotipy
import re

with open('dont commit\keys.txt', 'r') as filehandle:
    keys = json.load(filehandle)
    WEATHER_TOKEN = keys['WEATHER_API']
    OXFORD_APPID = keys['OXFORD_APPID']
    OXFORD_TOKEN = keys['OXFORD_TOKEN']
    NAVER_APPID = keys['NAVER_APPID']
    NAVER_TOKEN = keys['NAVER_TOKEN']
    LASTFM_APPID = keys['LASTFM_APIKEY']
    LASTFM_TOKEN = keys['LASTFM_SECRET']
    TIMEZONE_API_KEY = keys['TIMEZONEDB_API_KEY']
    SPOTIFY_CLIENT_ID = keys['SPOTIFY_CLIENT_ID']
    SPOTIFY_CLIENT_SECRET = keys['SPOTIFY_CLIENT_SECRET']


class Apis:

    def __init__(self, client):
        self.client = client

    @commands.command(name='weather', brief='Get the weather of a city')
    async def weather(self, ctx, *args):
        print(f"{ctx.message.author} >weather {args}")
        # noinspection PyBroadException
        try:
            city = " ".join(args).capitalize().replace('"', '')
            response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}"
                                    f"&appid={WEATHER_TOKEN}&units=metric")
            rescode = response.status_code
            print(f"requested weather for {city} with rescode {rescode}")
            if rescode == 200:
                weather_data = json.loads(response.content.decode('utf-8'))
                weather = weather_data['weather'][0]['description'].capitalize()
                temperature = weather_data['main']['temp']
                temperature_f = (temperature * (9.0 / 5.0) + 32)
                country = weather_data['sys']['country']
                city = weather_data['name']
                time = get_timezone(weather_data['coord'])
                await ctx.send(f":flag_{country.lower()}: `{city}, {country} — {weather}, "
                               f"{temperature:.1f} °C / {temperature_f:.1f} °F, local time: {time}`\n")
            else:
                await ctx.send(f"Error: status code {rescode}")
        except Exception as error:
            await ctx.send(f"Error: {error}")

    @commands.command(name='define', brief='Search from oxford dictionary')
    async def define(self, ctx, *args):
        print(f"{ctx.message.author} >define {args}")
        search_string = ' '.join(args).lower()
        api_url = 'https://od-api.oxforddictionaries.com:443/api/v1'
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
                    definitions_embed.add_field(name=entry["type"], value=entry["definition"].capitalize(),
                                                inline=False)

                await ctx.send(embed=definitions_embed)
            except Exception as e:
                print(e)
                await ctx.send('Error: no definition found for ' + search_string)
        else:
            await ctx.send('Error: status code' + str(id_response.status_code))

    @commands.command(name="urban", brief="Search from urban dictionary")
    async def urban(self, ctx, *args):
        print(f"{ctx.message.author} >urban {args}")
        search_string = " ".join(args)
        url = "https://mashape-community-urban-dictionary.p.mashape.com/define?term="
        response = requests.get(url + search_string, headers={"X-Mashape-Key":
                                                                  "w3TR0XTmB3mshcxWHQNKxiVWSuUtp1nqnlzjsnoZ6d0yZ1MJAT",
                                                              "Accept": "text/plain"})
        if response.status_code == 200:
            message = discord.Embed(colour=discord.Colour.orange())
            message.set_author(name=search_string.capitalize(), icon_url="https://i.imgur.com/yMwpnBe.png")

            json_data = json.loads(response.content.decode('utf-8'))
            # print(json.dumps(json_data, indent=4))

            if json_data['list']:
                word = json_data['list'][0]
                definition = word['definition'].replace("]", "").replace("[", "")
                example = word['example'].replace("]", "").replace("[", "")
                time = word['written_on'][:9].replace("-", "/")
                message.description = f"{definition}"
                message.add_field(name="Example", value=example)
                message.set_footer(text=f"by {word['author']} on {time}")
                await ctx.send(embed=message)
            else:
                await ctx.send("No definition found for " + search_string)
        else:
            await ctx.send("Error: " + str(response.status_code))

    @commands.command(name='translate', brief='Korean / Japanese / English Translator')
    async def translate(self, ctx, *args):
        print(f"{ctx.message.author} >translate {args}")
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
        api_url = 'https://openapi.naver.com/v1/papago/n2mt'
        request = urllib.request.Request(api_url)
        request.add_header('X-Naver-Client-Id', NAVER_APPID)
        request.add_header('X-Naver-Client-Secret', NAVER_TOKEN)
        response = urllib.request.urlopen(request, data=query.encode('utf-8'))
        rescode = response.getcode()
        if rescode == 200:
            response_body = json.loads(response.read().decode('utf-8'))
            translation = response_body['message']['result']['translatedText']
            await ctx.send(translation)
        else:
            print('Error Code:' + str(rescode))
            print(response)

    @commands.command(name='spotify', brief='Analyze a spotify playlist from URI')
    async def spotify(self, ctx, url=None, amount=10):
        print(f"{ctx.message.author} >spotify {url}")
        try:
            if url.startswith("https://open."):
                # its playlist link
                user_id = re.search(r'user/(.*?)/playlist', url).group(1)
                playlist_id = re.search(r'playlist/(.*?)\?', url).group(1)
            else:
                # its URI (probably)
                data = url.split(":")
                playlist_id = data[4]
                user_id = data[2]
        except Exception:
            await ctx.send("Usage: `>spotify {url/URI} {amount to show}(optional)`\n"
                           "How to get Spotify URI?: Right click playlist -> Share -> Copy Spotify URI")
            return

        try:
            if amount > 50:
                amount = 50
        except IndexError:
            amount = 10

        token = util.oauth2.SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
        cache_token = token.get_access_token()
        spotify = spotipy.Spotify(cache_token)
        tracks_per_request = 100
        results = []

        playlist_data = spotify.user_playlist(user_id, playlist_id)
        playlist_name = playlist_data['name']
        playlist_owner = playlist_data['owner']['display_name']
        playlist_image = playlist_data['images'][0]['url']

        this_request_results = spotify.user_playlist_tracks(user_id, playlist_id, limit=tracks_per_request,
                                                            offset=0)["items"]
        for i in range(len(this_request_results)):
            results.append(this_request_results[i])
        while len(this_request_results) >= tracks_per_request:
            this_request_results = spotify.user_playlist_tracks(user_id, playlist_id, limit=tracks_per_request,
                                                                offset=len(results))["items"]
            for i in range(len(this_request_results)):
                results.append(this_request_results[i])

        artists_dict = {}
        total = 0
        for i in range(len(results)):
            artist = results[i]["track"]["artists"][0]["name"]
            if artist in artists_dict:
                artists_dict[artist] += 1
            else:
                artists_dict[artist] = 1
            total += 1

        count = 0
        description = ""
        for item in sorted(artists_dict.items(), key=lambda v: v[1], reverse=True):
            if count < amount:
                percentage = (item[1] / total) * 100
                description += f"{item[1]} tracks — {percentage:.2f}% — {item[0]}\n"
                count += 1
            else:
                break

        message = discord.Embed(colour=discord.Colour.green())
        message.set_author(name=f"{playlist_name} · by {playlist_owner}",
                           icon_url="https://i.imgur.com/tN20ywg.png")
        message.set_thumbnail(url=playlist_image)
        message.title = "Artist distribution:"
        message.set_footer(text=f"Total tracks in this playlist: {total}")
        message.description = description

        await ctx.send(embed=message)

    @commands.command(name="convert", brief="convert units")
    async def convert(self, ctx, *args):
        print(f"{ctx.message.author} >convert {args}")
        source_quantity = args[0]
        source_unit, source_name = get_ucum_code(args[1])
        target_unit, target_name = get_ucum_code(args[len(args)-1])

        base_url = "https://ucum.nlm.nih.gov/ucum-service/v1/ucumtransform/"
        request_format = f"{source_quantity}/from/{source_unit}/to/{target_unit}"
        print(request_format)

        response = requests.get(base_url + request_format, headers={"Accept": "application/json"})
        if response.status_code == 200:
            json_data = json.loads(response.content.decode('utf-8'))
            print(json.dumps(json_data, indent=4))
            converted_quantity = json_data['UCUMWebServiceResponse']['Response']['ResultQuantity']

            await ctx.send(f"{source_quantity} {source_name} in {target_name} is {converted_quantity}")
        else:
            await ctx.send(f"Error {response.status_code}")


def get_timezone(coord):
    url = f"http://api.timezonedb.com/v2.1/get-time-zone?key={TIMEZONE_API_KEY}&format=json&by=position&" \
          f"lat={coord['lat']}&lng={coord['lon']}"
    response = requests.get(url)
    if response.status_code == 200:
        json_data = json.loads(response.content.decode('utf-8'))
        time = json_data['formatted'].split(" ")
        return time[1]
    else:
        return f"<error{response.status_code}>"


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
        return response_body['langCode']
    else:
        print('Error Code (detect_language):' + str(rescode))
        return None


def get_ucum_code(search_query):
    url = "https://clinicaltables.nlm.nih.gov/api/ucum/v3/search?terms="
    response = requests.get(url + search_query)
    if response.status_code == 200:
        json_data = json.loads(response.content.decode('utf-8'))
        ucum_code = json_data[3][0][0]
        name = json_data[3][0][1]
        print(name + " - " + ucum_code)
        return urllib.parse.quote_plus(ucum_code), name
    else:
        print(f"Error getting ucum code for {search_query}")


def setup(client):
    client.add_cog(Apis(client))
