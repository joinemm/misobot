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
import tweepy
from tweepy import OAuthHandler
import os
import html

keys = os.environ
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
TWITTER_CKEY = keys['TWITTER_CONSUMER_KEY']
TWITTER_CSECRET = keys['TWITTER_CONSUMER_SECRET']

auth = OAuthHandler(TWITTER_CKEY, TWITTER_CSECRET)
#auth.set_access_token(access_token, access_secret)
twt = tweepy.API(auth)

papago_pairs = ['ko/en', 'ko/ja', 'ko/zh-cn', 'ko/zh-tw', 'ko/vi', 'ko/id', 'ko/de', 'ko/ru', 'ko/es', 'ko/it',
                'ko/fr', 'en/ja', 'ja/zh-cn', 'ja/zh-tw', 'zh-cn/zh-tw', 'en/ko', 'ja/ko', 'zh-cn/ko', 'zh-tw/ko',
                'vi/ko', 'id/ko', 'th/ko', 'de/ko', 'ru/ko', 'es/ko', 'it/ko', 'fr/ko', 'ja/en', 'zh-cn/ja',
                'zh-tw/ja', 'zh-tw/zh-tw']

def load_data():
    with open('data/users.json', 'r') as filehandle:
        data = json.load(filehandle)
        return data


def save_data(users_json):
    with open('data/users.json', 'w') as filehandle:
        json.dump(users_json, filehandle, indent=4)

class Apis:

    def __init__(self, client):
        self.client = client
        self.logger = misolog.create_logger(__name__)

    @commands.command()
    async def weather(self, ctx, *args):
        """Get weather of a location"""
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

    @commands.command(aliases=['hs'])
    async def horoscope(self, ctx, setting=None, *args):
        self.logger.info(misolog.format_log(ctx, f""))
        hs = ['aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo', 'libra', 'scorpio', 'sagittarius', 'capricorn',
              'aquarius', 'pisces']
        user = str(ctx.message.author.id)
        data = load_data()
        if setting == "set":
            if args[0].lower() in hs:
                sign = args[0].lower()
            else:
                await ctx.send(f"`{args[0]}` is not a valid sunsign! use `>horoscope help` for a list of sunsigns.")
                return
            # set sign
            if not user in data['users']:
                data['users'][user] = {}
            data['users'][user]['sunsign'] = sign
            await ctx.send(f"Sunsign saved as `{sign}`")
            save_data(data)
            return
        elif setting == "help":
            list = "Aries (Mar 21-Apr 19)\nTaurus (Apr 20-May 20)\nGemini (May 21-June 20)\nCancer (Jun 21-Jul 22)\n" \
                   "Leo (Jul 23-Aug 22)\nVirgo (Aug 23-Sep 22)\nLibra (Sep 23-Oct 22)\nScorpio (Oct 23-Nov 21)\n" \
                   "Sagittarius (Nov 22-Dec 21)\nCapricorn (Dec 22-Jan 19)\nAquarius (Jan 20-Feb 18)\n" \
                   "Pisces (Feb 19-Mar 20)"
            content = discord.Embed()
            content.title = f"Sunsign list"
            content.description = list
            await ctx.send(embed=content)
            return
        elif setting is not None:
            # chosen sign
            if setting in hs:
                sign = setting
            else:
                await ctx.send(f"`{setting}` is not a valid sunsign! use `>horoscope help` for a list of sunsigns.")
                return
        else:
            # get user's sign
            try:
                sign = data['users'][user]['sunsign']
            except KeyError:
                await ctx.send("Please save your sunsign using `>horoscope set`\n"
                               "use `>horoscope help` if you don't know which one you are.")
                return

        url = f"http://theastrologer-api.herokuapp.com/api/horoscope/{sign}/today"
        response = requests.get(url)
        response_data = json.loads(response.content.decode('utf-8'))
        content = discord.Embed()
        content.title = response_data['sunsign']
        content.set_footer(text=response_data['date'])
        content.add_field(name='Mood', value=response_data['meta']['mood'].capitalize(), inline=True)
        content.add_field(name='Keywords', inline=True,
                          value=", ".join([x.capitalize() for x in response_data['meta']['keywords'].split(", ")]))
        content.add_field(name='Intensity', value=response_data['meta']['intensity'], inline=True)
        content.add_field(name='Horoscope', value=response_data['horoscope'].split("(c)")[0])
        await ctx.send(embed=content)

    @commands.command()
    async def define(self, ctx, *args):
        """Search from oxford dictionary"""
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

    @commands.command()
    async def urban(self, ctx, *args):
        """Search from urban dictionary"""
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

    @commands.command(aliases=['tr', 'trans'])
    async def translate(self, ctx, *text):
        """Translator that uses naver papago when possible, using google translator otherwise"""
        if text[0] == "help":
            self.logger.info(misolog.format_log(ctx, f"help"))
            await ctx.send('Format: `>translate source/target "text"`\n'
                           'Example: `>translate ko/en 안녕하세요`\n\n'
                           'Leave source empty to detect language automatically.\n'
                           'Example: `>translate /en こんにちは`\n\n'
                           'When no language codes given, defaults to detected -> english.\n'
                           'Example: `>translate ㅋㅋㅋ`')
            return
        if "/" in text[0]:
            source, target = text[0].split("/")
            text = text[1:]
            if source == "":
                source = self.detect_language(" ".join(text))
            if target == "":
                target = "en"
        else:
            source = self.detect_language(" ".join(text))
            target = "en"
        query_text = " ".join(text)
        language_pair = f"{source}/{target}"
        # we have language and query, now choose the appropriate translator

        if language_pair in papago_pairs:
            # use papago
            self.logger.info(misolog.format_log(ctx, f"papago [{language_pair}]"))
            query = f"source={source}&target={target}&text={query_text}"
            api_url = 'https://openapi.naver.com/v1/papago/n2mt'
            request = urllib.request.Request(api_url)
            request.add_header('X-Naver-Client-Id', NAVER_APPID)
            request.add_header('X-Naver-Client-Secret', NAVER_TOKEN)
            response = urllib.request.urlopen(request, data=query.encode('utf-8'))
            data = json.loads(response.read().decode('utf-8'))
            translation = data['message']['result']['translatedText']

        else:
            # use google
            self.logger.info(misolog.format_log(ctx, f"google [{language_pair}]"))
            url = f"https://translation.googleapis.com/language/translate/v2?key={GOOGLE_API_KEY}" \
                  f"&model=nmt&target={target}&source={source}&q={query_text}"
            response = requests.get(url)
            data = json.loads(response.content.decode('utf-8'))
            translation = html.unescape(data['data']['translations'][0]['translatedText'])

        await ctx.send(f"`{source}->{target}` " + translation)

    @commands.command()
    async def spotify(self, ctx, url=None, amount=10):
        """Analyze a spotify playlist from URI"""
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
        """Converts various units"""
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
    async def color(self, ctx, *args):
        """Get a hex color, the color of discord user, or a random color."""
        if args[0] == "random":
            colors = []
            try:
                amount = int(args[1])
            except IndexError:
                amount = 1
            for i in range(amount):
                colors += ["{:06x}".format(random.randint(0, 0xFFFFFF))]
        elif ctx.message.mentions:
            colors = [str(x.color).replace("#", "") for x in ctx.message.mentions]
        else:
            colors = [x.replace("#", "") for x in args]
        content = discord.Embed(colour=int(colors[0], 16))
        if len(colors) == 1:
            color = colors[0]
            url = f"http://thecolorapi.com/id?hex={color}&format=json"
            response = requests.get(url=url)
            if response.status_code == 200:
                data = json.loads(response.content.decode('utf-8'))
                hexvalue = data['hex']['value']
                rgbvalue = data['rgb']['value']
                name = data['name']['value']
                image_url = f"http://www.colourlovers.com/img/{color}/200/200/color.png"
                content.title = name
                content.description = f"{hexvalue} - {rgbvalue}"
            else:
                self.logger.error(misolog.format_log(ctx, f"color={color}&statuscode={response.status_code}"))
                await ctx.send(f"Error {response.status_code} on color {color}")
                return
        else:
            palette = ""
            for color in colors:
                url = f"http://thecolorapi.com/id?hex={color}&format=json"
                response = requests.get(url=url)
                if response.status_code == 200:
                    data = json.loads(response.content.decode('utf-8'))
                    hexvalue = data['hex']['value']
                    rgbvalue = data['rgb']['value']
                    name = data['name']['value']
                    content.add_field(name=name, value=f"{hexvalue}")
                    palette += color + "/"
                else:
                    self.logger.error(misolog.format_log(ctx, f"color={color}&statuscode={response.status_code}"))
                    await ctx.send(f"Error {response.status_code} on color {color}")
                    return
            image_url = f"https://www.colourlovers.com/paletteImg/{palette}palette.png"

        content.set_image(url=image_url)
        await ctx.send(embed=content)
        self.logger.info(misolog.format_log(ctx, f"colors={colors}"))

    @commands.command()
    async def question(self, ctx, *args):
        """Ask something from wolfram alpha"""
        query = " ".join(args)
        url = f"http://api.wolframalpha.com/v1/result?appid={WOLFRAM_APPID}&i={query}&output=json"
        response = requests.get(url.replace("+", "%2B"))
        if response.status_code == 200:
            result = response.content.decode('utf-8')
            self.logger.info(misolog.format_log(ctx, f""))
        else:
            result = "Sorry I did not understand your question."
            self.logger.warning(misolog.format_log(ctx, f"Invalid question"))

        await ctx.send(f"**{result}**")

    @commands.command()
    async def twitter(self, ctx, tweet_url, delete=None):
        """Get all the images from a tweet"""
        self.logger.info(misolog.format_log(ctx, f""))
        if "status" in tweet_url:
            tweet_id = re.search(r'status/(\d+)', tweet_url).group(1)
            tweet = twt.get_status(tweet_id)
        else:
            tweet = twt.get_status(tweet_url, tweet_mode='extended')

        media_files = []
        try:
            media = tweet.extended_entities.get('media', [])
        except AttributeError:
            await ctx.send("This tweet appears to contain no media!")
            return
        hashtags = []
        for hashtag in tweet.entities.get('hashtags', []):
            hashtags.append(f"#{hashtag['text']}")
        for i in range(len(media)):
            media_url = media[i]['media_url']
            video_url = None
            if not media[i]['type'] == "photo":
                video_urls = media[i]['video_info']['variants']
                largest_rate = 0
                for x in range(len(video_urls)):
                    if video_urls[x]['content_type'] == "video/mp4":
                        if video_urls[x]['bitrate'] > largest_rate:
                            largest_rate = video_urls[x]['bitrate']
                            video_url = video_urls[x]['url']
                            media_url = video_urls[x]['url']
            media_files.append((" ".join(hashtags), media_url, video_url))

        for file in media_files:
            content = discord.Embed(colour=int(tweet.user.profile_link_color, 16))
            content.set_image(url=file[1])
            content.set_author(icon_url=tweet.user.profile_image_url, name=f"@{tweet.user.screen_name}\n{file[0]}",
                               url=f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")

            await ctx.send(embed=content)

            if file[2] is not None:
                #content.description = f"Contains video/gif [Click here to view]({file[2]})"
                await ctx.send(file[2])

        if delete == "delete":
            await ctx.message.delete()

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
        url = f"https://translation.googleapis.com/language/translate/v2/detect?key={GOOGLE_API_KEY}" \
              f"&q={string}"
        response = requests.get(url)
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'))
            return data['data']['detections'][0][0]['language']
        else:
            self.logger.error(f"language detection error {str(response.status_code)}")
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
