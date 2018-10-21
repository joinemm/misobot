import json
import urllib.parse
import urllib.request
import discord
import requests
from discord.ext import commands

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


class Apis:

    def __init__(self, client):
        self.client = client

    @commands.command(name='weather', brief='Gets the weather of a given city')
    async def weather(self, ctx, *args):
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
                # (0°C × 9/5) + 32 = 32°F
                await ctx.send(f":flag_{country.lower()}: `{city}, {country} — {weather}, "
                               f"{temperature:.1f} °C / {temperature_f:.1f} °F, local time: {time}`\n")
            else:
                await ctx.send(f"Error: status code {rescode}")
        except Exception as error:
            await ctx.send(f"Error: {error}")

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
                    definitions_embed.add_field(name=entry["type"], value=entry["definition"].capitalize(),
                                                inline=False)

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

    @commands.command()
    async def spotify(self, ctx, *args):
        print()
        # soon tm


def get_timezone(coord):
    url = f"http://api.timezonedb.com/v2.1/get-time-zone?key={TIMEZONE_API_KEY}&format=json&by=position&" \
          f"lat={coord['lat']}&lng={coord['lon']}"
    response = requests.get(url)
    json_data = json.loads(response.content.decode('utf-8'))
    time = json_data['formatted'].split(" ")
    return time[1]


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
    client.add_cog(Apis(client))
