from discord.ext import commands
import requests
import json

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

    @commands.command(name="fm", brief="lastfm data", aliases=["Fm", "FM"])
    async def fm(self, ctx, *args):
        print(f"{ctx.message.author} >fm {args}")
        method_call = ""
        if len(args) > 0:

            try:
                method_call = args[0]
                if method_call in ["set"]:
                    method = "user.getinfo"
                    try:
                        fm_data = get_fm_data(method, args[1])
                        username = fm_data['user']['name']
                        playcount = fm_data['user']['playcount']
                        profile_url = fm_data['user']['url']

                        # save username here
                        users_json['users'][str(ctx.message.author.id)] = {'lastfm_username': args[1]}
                        save_data()

                        await ctx.send(f"username saved as {username}\nTotal scrobbles: {playcount}\n{profile_url}")
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
                    await ctx.send(f"argument {args[0]} not found.")
                    return
                print(method)
            except IndexError:
                method = "user.getinfo"

            try:
                amount = int(args[len(args)-1])
                if amount > 50:
                    amount = 50
                    print("max amount is 50")
            except Exception:
                amount = 10

            try:
                timeframe = args[1]
                if timeframe in ["week", "7day"]:
                    period = "7day"
                elif timeframe in ["month", "30day"]:
                    period = "1month"
                elif timeframe in ["year"]:
                    period = "12month"
                elif timeframe in ["alltime", "all"]:
                    period = "overall"
                else:
                    # await ctx.send(f"{args[1]} is not a valid timeframe.")
                    # return
                    print("not a valid timeframe")
                    period = "overall"
                print(period)
            except IndexError:
                period = "overall"

        else:
            # no arguments
            print("no arguments given")
            await ctx.send("Usage: >fm {set, nowplaying, recent, toptracks} {timeframe}")
            return
        try:
            user = users_json["users"][str(ctx.message.author.id)]['lastfm_username']
        except Exception:
            await ctx.send("No username found in database, please use >fm set {username}")
            return

        # all arguments parsed, get data
        fm_data = get_fm_data(method, user, period)

        # parse data and send it

        if method_call == "recent":
            total = 0
            message = "```"
            tracks = fm_data['recenttracks']['track']
            for i in range(amount):
                artist = tracks[i]['artist']['#text']
                album = tracks[i]['album']['#text']
                name = tracks[i]['name']
                line = f"\n{artist} — {name}"
                message += line
                total += 1
            message += "```"
            await ctx.send(f"recent {total} tracks for {user}:" + message)

        elif method_call == "nowplaying":
            tracks = fm_data['recenttracks']['track']
            artist = tracks[0]['artist']['#text']
            album = tracks[0]['album']['#text']
            name = tracks[0]['name']
            try:
                playing = tracks[0]['@attr']['nowplaying']
                message = f":notes: now playing: {artist} — {name}"
            except KeyError:
                message = f"most recent track: {artist} — {name}"
            await ctx.send(message)

        elif method_call == "toptracks":
            total = 0
            message = "```"
            tracks = fm_data['toptracks']['track']
            largest = len(tracks[0]['playcount'])
            for i in range(amount):
                artist = tracks[i]['artist']['name']
                name = tracks[i]['name']
                plays = tracks[i]['playcount']
                rank = tracks[i]['@attr']['rank']
                line = f"\n{rank:>2}. {plays:{largest}} plays - {name} — {artist}"
                message += line
                total += 1
            message += "```"
            await ctx.send(f"{total} top tracks for {user} in {period}:" + message)

        elif method_call == "topartists":
            total = 0
            message = "```"
            artists = fm_data['topartists']['artist']
            largest = len(artists[0]['playcount'])
            for i in range(amount):
                artist = artists[i]['name']
                plays = artists[i]['playcount']
                rank = artists[i]['@attr']['rank']
                line = f"\n{rank:>2}. {plays:{largest}} plays - {artist}"
                message += line
                total += 1
            message += "```"
            await ctx.send(f"{total} top artists for {user} in {period}:" + message)

        elif method_call == "topalbums":
            total = 0
            message = "```"
            albums = fm_data['topalbums']['album']
            largest = len(albums[0]['playcount'])
            for i in range(amount):
                album = albums[i]['name']
                artist = albums[i]['artist']['name']
                plays = albums[i]['playcount']
                rank = albums[i]['@attr']['rank']
                line = f"\n{rank:>2}. {plays:{largest}} plays - {album} — {artist}"
                message += line
                total += 1
            message += "```"
            await ctx.send(f"{total} top albums for {user} in {period}:" + message)

    @commands.command()
    async def fmgeo(self, ctx, *args):
        # >fmgeo toptracks finland
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
