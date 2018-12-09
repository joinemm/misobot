import json
import urllib.parse
import urllib.request
import discord
import requests
from discord.ext import commands
import spotipy.util as util
import spotipy
import re
from datetime import datetime
from utils import logger as misolog
import random

with open('dont commit\keys.txt', 'r') as filehandle:
    keys = json.load(filehandle)
    OXFORD_APPID = keys['OXFORD_APPID']
    OXFORD_TOKEN = keys['OXFORD_TOKEN']
    NAVER_APPID = keys['NAVER_APPID']
    NAVER_TOKEN = keys['NAVER_TOKEN']
    LASTFM_APPID = keys['LASTFM_APIKEY']
    LASTFM_TOKEN = keys['LASTFM_SECRET']
    TIMEZONE_API_KEY = keys['TIMEZONEDB_API_KEY']
    SPOTIFY_CLIENT_ID = keys['SPOTIFY_CLIENT_ID']
    SPOTIFY_CLIENT_SECRET = keys['SPOTIFY_CLIENT_SECRET']
    GOOGLE_API_KEY = keys['GOOGLE_KEY']
    DARKSKY_API_KEY = keys['DARK_SKY_KEY']
    STEAM_API_KEY = keys['STEAM_WEB_API_KEY']
    WOLFRAM_APPID = keys['WOLFRAM_APPID']


class Apis:

    def __init__(self, client):
        self.client = client
        self.logger = misolog.create_logger(__name__)

    @commands.command(name='weather', brief='dark sky weather')
    async def weather(self, ctx, *args):
        self.logger.info(misolog.format_log(ctx, f""))
        address = "+".join(args)
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_API_KEY}"
        response = requests.get(url=url)
        if response.status_code == 200:
            json_data = json.loads(response.content.decode('utf-8'))['results'][0]
            # print(json.dumps(json_data, indent=4))
            formatted_name = json_data['formatted_address']
            lat = json_data['geometry']['location']['lat']
            lon = json_data['geometry']['location']['lng']
            for comp in json_data['address_components']:
                if 'country' in comp['types']:
                    country = comp['short_name'].lower()

            # we have lat and lon now, plug them into dark sky
            response = requests.get(url=f"https://api.darksky.net/forecast/{DARKSKY_API_KEY}/{lat},{lon}?units=si")
            if response.status_code == 200:
                json_data = json.loads(response.content.decode('utf-8'))['currently']
                time = self.get_timezone({'lat': lat, 'lon': lon})
                temperature = json_data['temperature']
                temperature_f = (temperature * (9.0 / 5.0) + 32)
                summary = json_data['summary']
                windspeed = json_data['windSpeed']

                message = discord.Embed(color=discord.Color.dark_purple())
                message.description = f":flag_{country}: **{formatted_name}**\n" \
                                      f"**{summary}**\n" \
                                      f"Temperature: **{temperature} °C / {temperature_f:.2f} °F**\n" \
                                      f"Wind speed: **{windspeed} m/s**\n" \
                                      f"Local time: **{time}**\n"

                await ctx.send(embed=message)

    @commands.command(name='define', brief='Search from oxford dictionary')
    async def define(self, ctx, *args):
        self.logger.info(misolog.format_log(ctx, f""))
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
        self.logger.info(misolog.format_log(ctx, f""))
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
        self.logger.info(misolog.format_log(ctx, f""))
        search_string = urllib.parse.quote(' '.join(args))
        detected_lang = self.detect_language(search_string)
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
        self.logger.info(misolog.format_log(ctx, f""))
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

    @commands.command(name="convert")
    async def convert(self, ctx, *args):
        """Convert various units, C to F doesn't work"""
        source_quantity = args[0]
        source_unit, source_name = self.get_ucum_code(args[1])
        target_unit, target_name = self.get_ucum_code(args[len(args)-1])

        base_url = "https://ucum.nlm.nih.gov/ucum-service/v1/ucumtransform/"
        request_format = f"{source_quantity}/from/{source_unit}/to/{target_unit}"

        response = requests.get(base_url + request_format, headers={"Accept": "application/json"})
        if response.status_code == 200:
            json_data = json.loads(response.content.decode('utf-8'))
            # print(json.dumps(json_data, indent=4))
            try:
                converted_quantity = json_data['UCUMWebServiceResponse']['Response']['ResultQuantity']
                await ctx.send(f"**{source_quantity} {source_name}** is **{converted_quantity} {target_name}**")
                self.logger.info(misolog.format_log(ctx, f"from={source_name}[{source_quantity}], "
                                                         f"to={target_name}[{converted_quantity}]"))
            except TypeError:
                await ctx.send(f"```{json_data['UCUMWebServiceResponse']['Response']}```")
                self.logger.error(misolog.format_log(ctx, json_data['UCUMWebServiceResponse']['Response']))

        else:
            await ctx.send(f"Error {response.status_code}")

    @commands.command(name="currency")
    async def currency(self, ctx, *args):
        """Perform currency conversion"""
        try:
            source_q = float(args[0])
            source_curr = args[1]
            target_curr = args[3]
        except IndexError:
            await ctx.send("Invalid syntax! example: `>currency 20 usd in eur`")
            self.logger.warning(misolog.format_log(ctx, f"Invalid Syntax"))
            return

        response = requests.get(url=f"https://free.currencyconverterapi.com/api/v6/convert"
                                    f"?q={source_curr}_{target_curr}")
        if response.status_code == 200:
            json_data = json.loads(response.content.decode('utf-8'))
            if json_data['results']:
                conversion = json_data['results'][f'{source_curr}_{target_curr}'.upper()]
                rate = conversion['val']
                target_q = source_q*rate
                await ctx.send(f"**{source_q:.2f} {conversion['fr']}** is **{target_q:.2f} {conversion['to']}**")
                self.logger.info(misolog.format_log(ctx, f""))
            else:
                await ctx.send("Invalid currency code!")
                self.logger.warning(misolog.format_log(ctx, f"Invalid Currency"))

    @commands.command(name="color", aliases=["colour"])
    async def color(self, ctx, color, mode=None):
        """Get a hex color, the color of discord user, or a random color."""
        if color == "random":
            color = "{:06x}".format(random.randint(0, 0xFFFFFF))
        elif ctx.message.mentions:
            color = str(ctx.message.mentions[0].color).replace("#", "")
        url = f"http://thecolorapi.com/id?hex={color}&format=json"
        response = requests.get(url=url)
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'))
            if mode == "debug":
                await ctx.send(f"```json\n{json.dumps(data, indent=4)}\n```")
                return
            hexvalue = data['hex']['value']
            rgbvalue = data['rgb']['value']
            name = data['name']['value']
            image_url = f"http://www.colourlovers.com/img/{color}/200/200/color.png"

            content = discord.Embed(colour=int(color, 16))
            content.set_image(url=image_url)
            content.title = name
            content.description = f"{hexvalue} - {rgbvalue}"
            await ctx.send(embed=content)
            self.logger.info(misolog.format_log(ctx, f"color={hexvalue}"))
        else:
            self.logger.error(misolog.format_log(ctx, f"statuscode={response.status_code}"))

    @commands.command()
    async def question(self, ctx, *args):
        query = " ".join(args)
        url = f"http://api.wolframalpha.com/v1/result?appid={WOLFRAM_APPID}&i={query}&output=json"
        response = requests.get(url.replace("+", "%2B"))
        if response.status_code == 200:
            result = response.content.decode('utf-8')
            self.logger.info(misolog.format_log(ctx, f"Success"))
        else:
            result = "Sorry I did not understand your question."
            self.logger.warning(misolog.format_log(ctx, f"Invalid question"))

        await ctx.send(f"**{result}**")

    @commands.command(name="steam")
    async def steam(self, ctx, steam_id, *args):
        """Get steam profile data"""
        self.logger.info(misolog.format_log(ctx, f""))

        try:
            steam_id = int(steam_id)
        except ValueError:
            response = requests.get(url=f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1?"
                                        f"key={STEAM_API_KEY}&vanityurl={steam_id}")
            if response.status_code == 200:
                resolved = json.loads(response.content.decode('utf-8'))['response']
                if resolved['success'] == 1:
                    steam_id = resolved['steamid']
                else:
                    await ctx.send(f"Error: {resolved['message']} (ResolveVanityUrl)")
                    return
            else:
                await ctx.send(f"Error {response.status_code} (ResolveVanityUrl)")
                return

        response = requests.get(url=f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?"
                                    f"key={STEAM_API_KEY}&steamids={steam_id}&format=json")
        if response.status_code == 200:
            profile_json = json.loads(response.content.decode('utf-8'))['response']['players'][0]
        else:
            await ctx.send(f"Error {response.status_code} (GetPlayerSummaries)")
            return
        response = requests.get(url=f"http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?"
                                    f"key={STEAM_API_KEY}&steamid={steam_id}&format=json")
        if response.status_code == 200:
            recent_games_json = json.loads(response.content.decode('utf-8'))['response']
        else:
            await ctx.send(f"Error {response.status_code} (GetRecentlyPlayedGames)")
            return
        response = requests.get(url=f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?"
                                    f"key={STEAM_API_KEY}&steamid={steam_id}&format=json")
        if response.status_code == 200:
            owned_games_json = json.loads(response.content.decode('utf-8'))['response']
        else:
            await ctx.send(f"Error {response.status_code} (GetOwnedGames)")
            return

        message = discord.Embed(color=discord.Color.blue())
        try:
            if args[0] in ['top', "mostplayed", "topgames"]:
                print("soontm")
        except IndexError:
            # show profile

            created_at = datetime.utcfromtimestamp(int(profile_json['timecreated'])).strftime('%Y-%m-%d %H:%M:%S')
            profile_states = ["Offline", "Online", "Busy", "Away", "Snooze", "Looking to trade", "Looking to play"]
            recent_games_string = "N/A"
            total_playtime_2weeks = 0

            message.title = f"{profile_json['personaname']} ({profile_json['steamid']})"
            message.set_thumbnail(url=profile_json['avatarfull'])
            try:
                for i in range(recent_games_json['total_count']):
                    if i == 0:
                        recent_games_string = ""
                    total_playtime_2weeks += recent_games_json['games'][i]['playtime_2weeks']
                    recent_games_string += f"{recent_games_json['games'][i]['name']} - " \
                                           f"**{recent_games_json['games'][i]['playtime_2weeks']/60:.1f}** Hours " \
                                           f"(total **{recent_games_json['games'][i]['playtime_forever']/60:.1f}** hours)\n"

                message.add_field(name=f"Recently played - **{total_playtime_2weeks/60:.1f}** hours past two weeks",
                                  value=recent_games_string)
            except Exception as e:
                message.add_field(name=f"Recently played - **{total_playtime_2weeks/60:.1f}** hours past two weeks",
                                  value=str(e))

            try:
                total_playtime = 0
                games = []
                for i in range(owned_games_json['game_count']):
                    playtime = owned_games_json['games'][i]['playtime_forever']
                    total_playtime += playtime

                try:
                    state = f"In-Game: **{profile_json['gameextrainfo']}**"
                except KeyError:
                    state = f"State: {profile_states[profile_json['personastate']]}"

                try:
                    countrycode = profile_json['loccountrycode']
                except KeyError:
                    countrycode = "N/A"

                message.description = f"Country: **{countrycode}**\n" \
                                      f"{state}\n" \
                                      f"Owned games: **{owned_games_json['game_count']}**\n" \
                                      f"Total playtime: **{total_playtime/60:.1f} hours**\n" \
                                      f"Created at: {created_at}"
            except Exception as e:
                message.description = f"Error: {str(e)}"

        await ctx.send(embed=message)

    def get_timezone(self, coord):
        url = f"http://api.timezonedb.com/v2.1/get-time-zone?key={TIMEZONE_API_KEY}&format=json&by=position&" \
              f"lat={coord['lat']}&lng={coord['lon']}"
        response = requests.get(url)
        if response.status_code == 200:
            json_data = json.loads(response.content.decode('utf-8'))
            time = json_data['formatted'].split(" ")
            return ":".join(time[1].split(":")[:2])
        else:
            return f"<error{response.status_code}>"

    def detect_language(self, string):
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
            self.logger.error(f"response_status_code={str(rescode)}")
            return None

    def get_ucum_code(self, search_query):
        url = "https://clinicaltables.nlm.nih.gov/api/ucum/v3/search?terms="
        response = requests.get(url + search_query)
        if response.status_code == 200:
            json_data = json.loads(response.content.decode('utf-8'))
            ucum_code = json_data[3][0][0]
            name = json_data[3][0][1]
            return urllib.parse.quote_plus(ucum_code), name
        else:
            self.logger.error(f"query={search_query}")


def n_max_elements(list1, n):
    final_list = []
    for i in range(0, n):
        max1 = 0
        maxtuple = (0, 0)
        for j in range(len(list1)):
            if list1[j][1] > max1:
                max1 = list1[j][1]
                maxtuple = list1[j]

        list1.remove(maxtuple)
        final_list.append(maxtuple)

    return final_list


def setup(client):
    client.add_cog(Apis(client))
