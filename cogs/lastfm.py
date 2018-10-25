from discord.ext import commands
import requests
import json
import discord
from datetime import datetime

with open('dont commit\keys.txt', 'r') as keys_filehandle:
    keys = json.load(keys_filehandle)
    LASTFM_APPID = keys['LASTFM_APIKEY']
    LASTFM_TOKEN = keys['LASTFM_SECRET']


def load_data():
    with open('users.json', 'r') as filehandle:
        data = json.load(filehandle)
        print('users.json loaded')
        return data


def save_data():
    with open('users.json', 'w') as filehandle:
        json.dump(users_json, filehandle, indent=4)
        print('users.json saved')


users_json = load_data()


class Lastfm:

    def __init__(self, client):
        self.client = client

    @commands.command(name="fm", brief="Get user data from LastFM", aliases=["Fm", "FM"])
    async def fm(self, ctx, *args):
        print(f"{ctx.message.author} >fm {args}")
        if len(args) > 0:

            try:
                method_call = args[0]
                if method_call in ["set"]:
                    method = "user.getinfo"
                    try:
                        fm_data = get_fm_data(method, args[1])
                        username = fm_data['user']['name']
                        profile_url = fm_data['user']['url']
                        users_json['users'][str(ctx.message.author.id)] = {'lastfm_username': args[1]}
                        save_data()
                        await ctx.send(f"Username saved as {username}\n{profile_url}")
                        return
                    except IndexError:
                        await ctx.send("please give a username")
                        return
                elif method_call in ["np", "nowplaying"]:
                    method_call = "nowplaying"
                    method = "user.getrecenttracks"
                elif method_call in ["recent", "recents"]:
                    method_call = "recent"
                    method = "user.getrecenttracks"
                elif method_call in ["toptracks", "tt"]:
                    method_call = "toptracks"
                    method = "user.gettoptracks"
                elif method_call in ["topartists", "ta"]:
                    method_call = "topartists"
                    method = "user.gettopartists"
                elif method_call in ["topalbums", "talb"]:
                    method_call = "topalbums"
                    method = "user.gettopalbums"
                else:
                    await ctx.send(f'argument {args[0]} not found, use ">fm help" to get help')
                    return
            except IndexError:
                method = "user.getinfo"
                method_call = "userinfo"

            try:
                amount = int(args[len(args)-1])
                if amount > 50:
                    amount = 50
            except Exception:
                amount = 10

            try:
                timeframe = args[1]
                if timeframe in ["week", "7day"]:
                    period = "7day"
                elif timeframe in ["month", "30day"]:
                    period = "1month"
                elif timeframe in ["3month", "3months"]:
                    period = "3month"
                elif timeframe in ["halfyear", "6month"]:
                    period = "6month"
                elif timeframe in ["year"]:
                    period = "12month"
                elif timeframe in ["alltime", "all"]:
                    period = "overall"
                else:
                    period = "overall"
            except IndexError:
                period = "overall"

        else:
            # no arguments
            method = "user.getinfo"
            method_call = "userinfo"
            period = "overall"
            amount = 10
        try:
            user = users_json["users"][str(ctx.message.author.id)]['lastfm_username']
        except Exception:
            await ctx.send("No username found in database, please use >fm set {username}")
            return

        # all arguments parsed, get data based on the given arguments
        fm_data = get_fm_data(method, user, period)
        if fm_data is None:
            await ctx.send("Error getting data from LastFM")
            return

        # parse data and set embed settings
        message = discord.Embed(colour=discord.Colour.magenta())
        total = 0

        if method_call == "nowplaying":
            user_attr = fm_data['recenttracks']['@attr']
            tracks = fm_data['recenttracks']['track']
            artist = tracks[0]['artist']['#text']
            album = tracks[0]['album']['#text']
            if album == "":
                album = "<unknown album>"
            name = tracks[0]['name']
            message.description = album
            try:
                if tracks[0]['@attr']['nowplaying'] == "true":
                    message.set_author(name=f"{user_attr['user']} — Now Playing",
                                       icon_url=ctx.message.author.avatar_url)
                    message.title = f"{artist} — *{name}* :notes:"
                else:
                    await ctx.send("lastfm error :thinking:")
            except KeyError:
                message.set_author(name=f"{user_attr['user']} — Most recent track:",
                                   icon_url=ctx.message.author.avatar_url)
                message.title = f"{artist} — {name}"
            message.set_thumbnail(url=tracks[0]['image'][3]['#text'])

        elif method_call == "recent":
            user_attr = fm_data['recenttracks']['@attr']
            tracks = fm_data['recenttracks']['track']
            description = ""
            for i in range(amount):
                artist = tracks[i]['artist']['#text']
                album = tracks[i]['album']['#text']
                if album == "":
                    album = "<unknown album>"
                name = tracks[i]['name']
                description += f"**{artist}** — ***{name}***\n"
                total += 1
            message.description = description
            message.set_thumbnail(url=tracks[0]['image'][3]['#text'])
            message.set_footer(text=f"Total plays: {user_attr['total']}")
            message.set_author(name=f"{user_attr['user']} — {total} Recent tracks",
                               icon_url=ctx.message.author.avatar_url)

        elif method_call == "toptracks":
            user_attr = fm_data['toptracks']['@attr']
            tracks = fm_data['toptracks']['track']
            largest = len(tracks[0]['playcount'])
            description = ""
            for i in range(amount):
                artist = tracks[i]['artist']['name']
                name = tracks[i]['name']
                plays = tracks[i]['playcount']
                rank = tracks[i]['@attr']['rank']
                description += f"**{plays:{largest}}** plays - ***{name}*** — **{artist}**\n"
                total += 1
            message.description = description
            message.set_thumbnail(url=tracks[0]['image'][3]['#text'])
            message.set_footer(text=f"Total unique tracks: {user_attr['total']}")
            message.set_author(name=f"{user_attr['user']} — {total} Most played tracks {period}",
                               icon_url=ctx.message.author.avatar_url)

        elif method_call == "topartists":
            user_attr = fm_data['topartists']['@attr']
            artists = fm_data['topartists']['artist']
            largest = len(artists[0]['playcount'])
            description = ""
            for i in range(amount):
                artist = artists[i]['name']
                plays = artists[i]['playcount']
                rank = artists[i]['@attr']['rank']
                description += f"**{plays:{largest}}** plays — **{artist}**\n"
                total += 1
            message.description = description
            message.set_thumbnail(url=artists[0]['image'][3]['#text'])
            message.set_footer(text=f"Total unique artists: {user_attr['total']}")
            message.set_author(name=f"{user_attr['user']} — {total} Most played artists {period}",
                               icon_url=ctx.message.author.avatar_url)

        elif method_call == "topalbums":
            user_attr = fm_data['topalbums']['@attr']
            albums = fm_data['topalbums']['album']
            largest = len(albums[0]['playcount'])
            description = ""
            for i in range(amount):
                album = albums[i]['name']
                artist = albums[i]['artist']['name']
                plays = albums[i]['playcount']
                rank = albums[i]['@attr']['rank']
                description += f"**{plays:{largest}}** plays - ***{album}*** — **{artist}**\n"
                total += 1
            message.description = description
            message.set_thumbnail(url=albums[0]['image'][3]['#text'])
            message.set_footer(text=f"Total unique albums: {user_attr['total']}")
            message.set_author(name=f"{user_attr['user']} — {total} Most played albums {period}",
                               icon_url=ctx.message.author.avatar_url)

        elif method_call == "userinfo":
            username = fm_data['user']['name']
            playcount = fm_data['user']['playcount']
            profile_url = fm_data['user']['url']
            profile_pic_url = fm_data['user']['image'][3]['#text']
            timestamp = int(fm_data['user']['registered']['unixtime'])
            utc_time = datetime.utcfromtimestamp(timestamp)
            time = utc_time.strftime("%d/%m/%Y")

            message.set_author(name=f"{username}",
                               icon_url=ctx.message.author.avatar_url)
            message.add_field(name="LastFM profile", value=f"[link]({profile_url})", inline=True)
            message.add_field(name="Registered on", value=f"{time}", inline=True)
            message.set_thumbnail(url=profile_pic_url)
            message.set_footer(text=f"Total plays: {playcount}")

        # settings done, send embed
        await ctx.send(embed=message)

    @commands.command(name="fmgeo", brief="Get country specific data from LastFM")
    async def fmgeo(self, ctx, *args):
        try:
            method_call = args[0]
            country = " ".join(args[1:])
            if method_call in ["toptracks", "tt"]:
                url = f"http://ws.audioscrobbler.com/2.0/?method=geo.gettoptracks" \
                      f"&country={country}&api_key={LASTFM_APPID}&format=json"
                response = requests.get(url)
                if response.status_code == 200:
                    try:
                        message = "```"
                        rank = 0
                        fm_data = json.loads(response.content.decode('utf-8'))
                        tracks = fm_data['tracks']['track']
                        for i in range(10):
                            name = tracks[i]['name']
                            listeners = tracks[i]['listeners']
                            artist = tracks[i]['artist']['name']
                            rank += 1
                            line = f"\n{rank:>2}: {name} — {artist} — {listeners} listeners"
                            message += line
                        message += "```"
                        await ctx.send(f"top tracks for {country}:" + message)
                    except KeyError:
                        await ctx.send("invalid country code")
                else:
                    print(f"Error: status code {response.status_code}")

            elif method_call in ["topartists", "ta"]:
                url = f"http://ws.audioscrobbler.com/2.0/?method=geo.gettopartists" \
                      f"&country={country}&api_key={LASTFM_APPID}&format=json"
                response = requests.get(url)
                try:
                    if response.status_code == 200:
                        message = "```"
                        rank = 0
                        fm_data = json.loads(response.content.decode('utf-8'))
                        artists = fm_data['topartists']['artist']
                        for i in range(10):
                            name = artists[i]['name']
                            listeners = artists[i]['listeners']
                            rank += 1
                            line = f"\n{rank:>2}: {name} — {listeners} listeners"
                            message += line
                        message += "```"
                        await ctx.send(f"top artists for {country}:" + message)
                    else:
                        print(f"Error: status code {response.status_code}")

                except KeyError:
                    await ctx.send("invalid country code")
            else:
                await ctx.send("invalid syntax")
                return
        except IndexError:
            await ctx.send("invalid syntax")
            return


def get_fm_data(method, user, period="overall"):
    url = f"http://ws.audioscrobbler.com/2.0/?method={method}" \
          f"&user={user}&api_key={LASTFM_APPID}&format=json&period={period}"
    response = requests.get(url)
    if response.status_code == 200:
        fm_data = json.loads(response.content.decode('utf-8'))
        return fm_data
    else:
        print(f"Error: status code {response.status_code}")
        return None


def setup(client):
    client.add_cog(Lastfm(client))
