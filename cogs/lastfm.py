from discord.ext import commands
import requests
import json
import discord
from datetime import datetime
from utils import logger as misolog
import imgkit
import time as t
import os
import asyncio

keys = os.environ
LASTFM_APPID = keys['LASTFM_APIKEY']
LASTFM_TOKEN = keys['LASTFM_SECRET']


def load_data():
    with open('data/users.json', 'r') as filehandle:
        data = json.load(filehandle)
        return data


def save_data(users_json):
    with open('data/users.json', 'w') as filehandle:
        json.dump(users_json, filehandle, indent=4)


class LastFM:

    def __init__(self, client):
        self.client = client
        self.logger = misolog.create_logger(__name__)
        self.users_json = load_data()
        with open("html/fm_chart_flex.html", "r", encoding="utf-8") as file:
            self.chart_html_flex = file.read().replace('\n', '')

    @commands.command()
    async def fm(self, ctx, method=None, timeframe=None, *args):
        """Get user and song data from LastFM"""
        self.logger.info(misolog.format_log(ctx, f""))

        if method == "set":
            if timeframe is None:
                await ctx.send("Please give a username!")
                return

            content = self.userinfo(ctx, timeframe)
            if content is None:
                await ctx.send(f"ERROR: Invalid username `{timeframe}`")
                return

            self.users_json['users'][str(ctx.message.author.id)]['lastfm_username'] = timeframe
            save_data(self.users_json)
            await ctx.send(f"{ctx.message.author.mention} Username saved as {timeframe}", embed=content)
            self.users_json = load_data()
            return
        else:
            try:
                username = self.users_json['users'][str(ctx.message.author.id)]['lastfm_username']
            except KeyError:
                await ctx.send("No username found in database, please use >fm set [username]")
                return

        if method in ["np", "nowplaying"]:
            content = self.nowplaying(ctx, username)
            if content is not None:
                await ctx.send(embed=content)
            else:
                await ctx.send("LastFM Error")
        elif method in ["userinfo", "info", None]:
            content = self.userinfo(ctx, username)
            if content is not None:
                await ctx.send(embed=content)
            else:
                await ctx.send("LastFM Error")
            return
        elif method in ["help"]:
            help_msg = "```\n" \
                       ">fm       nowplaying (np)   week\n" \
                       "          recent (re)       month\n" \
                       "          toptracks (tt)    3month\n" \
                       "          topartists (ta)   6month\n" \
                       "          topalbums (talb)  year\n\n" \
                       ">fmchart  recent (re)        1x1\n" \
                       "          topalbums (talb)    :\n" \
                       "          topartists (ta)   14x14\n\n" \
                       ">fmartist [artist name]" \
                       "```"
            await ctx.send(help_msg)
            return

        else:

            period = get_period(timeframe)
            amount = 15
            try:
                amount = int(args[-1])
            except Exception:
                try:
                    amount = int(timeframe)
                except Exception:
                    pass

            current_page = 0

            if method in ["recent", "recents", "re"]:
                await  ctx.message.channel.trigger_typing()
                content, pages = self.recent_tracks(ctx, username, amount)

            elif method in ["toptracks", "tt"]:
                await ctx.message.channel.trigger_typing()
                content, pages = self.top_tracks(ctx, username, period, amount)

            elif method in ["topartists", "ta"]:
                await ctx.message.channel.trigger_typing()
                content, pages = self.top_artists(ctx, username, period, amount)

            elif method in ["topalbums", "talb"]:
                await ctx.message.channel.trigger_typing()
                content, pages = self.top_albums(ctx, username, period, amount)
            else:
                await ctx.send(f'Command `{method}` not found, use ">fm help" to get help')
                return

            if len(pages) > 1:
                content.set_footer(text=f"page {current_page + 1} of {len(pages)}")
            my_msg = await ctx.send(embed=content)

            if len(pages) > 1:

                def check(_reaction, _user):
                    return _reaction.message.id == my_msg.id and _reaction.emoji in ["⬅", "➡"] and not _user == self.client.user

                await my_msg.add_reaction("⬅")
                await my_msg.add_reaction("➡")

                while True:
                    try:
                        reaction, user = await self.client.wait_for('reaction_add', timeout=300.0, check=check)
                    except asyncio.TimeoutError:
                        return
                    else:
                        try:
                            if reaction.emoji == "⬅" and current_page > 0:
                                content.description = pages[current_page - 1]
                                current_page -= 1
                                await my_msg.remove_reaction("⬅", user)
                            elif reaction.emoji == "➡":
                                content.description = pages[current_page + 1]
                                current_page += 1
                                await my_msg.remove_reaction("➡", user)
                            else:
                                continue
                            content.set_footer(text=f"page {current_page+1} of {len(pages)}")
                            await my_msg.edit(embed=content)
                        except IndexError:
                            continue

    def userinfo(self, ctx, username):
        data = api_request({"user": username, "method": "user.getinfo"})
        if data is not None and not "error" in data:
            content = discord.Embed(colour=discord.Colour.magenta())
            username = data['user']['name']
            playcount = data['user']['playcount']
            profile_url = data['user']['url']
            profile_pic_url = data['user']['image'][3]['#text']
            timestamp = int(data['user']['registered']['unixtime'])
            utc_time = datetime.utcfromtimestamp(timestamp)
            time = utc_time.strftime("%d/%m/%Y")

            content.set_author(name=f"{username}",
                               icon_url=ctx.message.author.avatar_url)
            content.add_field(name="LastFM profile", value=f"[link]({profile_url})", inline=True)
            content.add_field(name="Registered on", value=f"{time}", inline=True)
            content.set_thumbnail(url=profile_pic_url)
            content.set_footer(text=f"Total plays: {playcount}")
            return content
        else:
            return None

    def nowplaying(self, ctx, username):
        data = api_request({"user": username, "method": "user.getrecenttracks"})
        if data is not None and not "error" in data:
            content = discord.Embed(colour=discord.Colour.magenta())
            user_attr = data['recenttracks']['@attr']
            tracks = data['recenttracks']['track']
            artist = escape(tracks[0]['artist']['#text'], 2)
            album = escape(tracks[0]['album']['#text'], 2)
            track = escape(tracks[0]['name'], 2)

            content.description = f"**{album}**"
            content.title = f"**{artist}** — ***{track}***"
            content.set_thumbnail(url=tracks[0]['image'][3]['#text'])

            trackdata = api_request({"user": username, "method": "track.getInfo", "artist": artist, "track": track})
            if trackdata is not None:
                trackdata = trackdata['track']
                try:
                    playcount = trackdata['userplaycount']
                    content.description = f"**{album}**\n{playcount} total plays"
                except KeyError:
                    pass
                tags = []
                for tag in trackdata['toptags']['tag']:
                    tags.append(tag['name'])

                if tags:
                    content.set_footer(text=", ".join(tags))

            state = "Most recent track:"
            if '@attr' in tracks[0]:
                if "nowplaying" in tracks[0]['@attr']:
                    state = "Now Playing"

            content.set_author(name=f"{user_attr['user']} — {state}:",
                               icon_url=ctx.message.author.avatar_url)
            return content
        else:
            return None

    def recent_tracks(self, ctx, username, amount):
        if amount > 200:
            amount = 200
        data = api_request({"user": username, "method": "user.getrecenttracks", "limit": amount})
        if data is not None and not "error" in data:
            content = discord.Embed(colour=discord.Colour.magenta())
            user_attr = data['recenttracks']['@attr']
            tracks = data['recenttracks']['track']
            description = []
            for i in range(amount):
                artist = escape(tracks[i]['artist']['#text'], 2)
                name = escape(tracks[i]['name'], 3)
                description.append(f"**{artist}** — ***{name}***")
            content.set_thumbnail(url=tracks[0]['image'][3]['#text'])
            content.set_footer(text=f"Total plays: {user_attr['total']}")
            content.set_author(name=f"{user_attr['user']} — {amount} Recent tracks",
                               icon_url=ctx.message.author.avatar_url)

            pages = create_pages(description)
            content.description = pages[0]
            return content, pages
        else:
            return None

    def top_artists(self, ctx, username, period, amount):
        data = api_request({"user": username, "method": "user.gettopartists", "limit": amount, "period": period})
        if data is not None and not "error" in data:
            content = discord.Embed(colour=discord.Colour.magenta())
            user_attr = data['topartists']['@attr']
            artists = data['topartists']['artist']
            description = []
            for i in range(amount):
                artist = escape(artists[i]['name'], 2)
                plays = escape(artists[i]['playcount'], 2)
                rank = artists[i]['@attr']['rank']
                description.append(f"**{plays}** plays — **{artist}**")
            content.set_thumbnail(url=artists[0]['image'][3]['#text'])
            content.set_footer(text=f"Total unique artists: {user_attr['total']}")
            content.set_author(name=f"{user_attr['user']} — {amount} Most played artists {period}",
                               icon_url=ctx.message.author.avatar_url)
            pages = create_pages(description)
            content.description = pages[0]
            return content, pages
        else:
            return None

    def top_albums(self, ctx, username, period, amount):
        data = api_request({"user": username, "method": "user.gettopalbums", "limit": amount, "period": period})
        if data is not None and not "error" in data:
            content = discord.Embed(colour=discord.Colour.magenta())
            user_attr = data['topalbums']['@attr']
            albums = data['topalbums']['album']
            description = []
            for i in range(amount):
                album = escape(albums[i]['name'], 3)
                artist = escape(albums[i]['artist']['name'], 2)
                plays = albums[i]['playcount']
                rank = albums[i]['@attr']['rank']
                description.append(f"**{plays}** plays - ***{album}*** — **{artist}**")
            content.description = description
            content.set_thumbnail(url=albums[0]['image'][3]['#text'])
            content.set_footer(text=f"Total unique albums: {user_attr['total']}")
            content.set_author(name=f"{user_attr['user']} — {amount} Most played albums {period}",
                               icon_url=ctx.message.author.avatar_url)
            pages = create_pages(description)
            content.description = pages[0]
            return content, pages
        else:
            return None

    def top_tracks(self, ctx, username, period, amount):
        data = api_request({"user": username, "method": "user.gettoptracks", "limit": amount, "period": period})
        if data is not None and not "error" in data:
            content = discord.Embed(colour=discord.Colour.magenta())
            user_attr = data['toptracks']['@attr']
            tracks = data['toptracks']['track']
            description = []
            for i in range(amount):
                artist = escape(tracks[i]['artist']['name'], 2)
                name = escape(tracks[i]['name'], 3)
                plays = tracks[i]['playcount']
                rank = tracks[i]['@attr']['rank']
                description.append(f"**{plays}** plays - **{artist}** — ***{name}***")
            content.description = description
            content.set_thumbnail(url=tracks[0]['image'][3]['#text'])
            content.set_footer(text=f"Total unique tracks: {user_attr['total']}")
            content.set_author(name=f"{user_attr['user']} — {amount} Most played tracks {period}",
                               icon_url=ctx.message.author.avatar_url)
            pages = create_pages(description)
            content.description = pages[0]
            return content, pages
        else:
            return None

    @commands.command()
    async def fmchart(self, ctx, method, timeframe="week", size="3x3", debug=False):
        timer_start = t.time()
        await  ctx.message.channel.trigger_typing()
        try:
            username = self.users_json['users'][str(ctx.message.author.id)]['lastfm_username']
        except KeyError:
            await ctx.send("No username found in database, please use >fm set [username]")
            return
        period = get_period(timeframe)
        size = int(size.split("x")[0])
        if size > 14:
            await ctx.send("```Error: Maximum supported chart size is 14x14```")
            return
        chart = [("N/A", "https://via.placeholder.com/300/?text=Miso+Bot")] * (size * size)
        if method in ["recent", "recents", "re"]:
            data = api_request({"user": username, "method": "user.getrecenttracks", "limit": (size * size)})
            chart_type = ""
            period = "recent"
            tracks = data['recenttracks']['track']
            for i in range(len(chart)):
                try:
                    artist = tracks[i]['artist']['#text']
                    name = tracks[i]['name']
                    chart[i] = (f"<br>{name} - {artist}", tracks[i]['image'][3]['#text'])
                except IndexError:
                    break

        elif method in ["topartists", "ta"]:
            data = api_request({"user": username, "method": "user.gettopartists", "limit": (size * size)})
            chart_type = " Artist"
            artists = data['topartists']['artist']
            for i in range(len(chart)):
                try:
                    artist = artists[i]['name']
                    plays = artists[i]['playcount']
                    chart[i] = (f"{plays} plays<br>{artist}", artists[i]['image'][3]['#text'])
                except IndexError:
                    break

        elif method in ["topalbums", "talb"]:
            data = api_request({"user": username, "method": "user.gettopalbums", "limit": (size * size)})
            chart_type = " Album"
            albums = data['topalbums']['album']
            for i in range(len(chart)):
                try:
                    album = albums[i]['name']
                    artist = albums[i]['artist']['name']
                    plays = albums[i]['playcount']
                    chart[i] = (f"{plays} plays<br>{album} - {artist}", albums[i]['image'][3]['#text'])
                except IndexError:
                    break
        else:
            await ctx.send(f'Command `{method}` not found for chart, use ">fm help" to get help')
            return

        arts = ""
        for i in range(len(chart)):
            arts += '<div class="art"><img src="{' + str(i) + '[1]}"><p class="label">{' + str(i) + '[0]}</p></div>'

        dimensions = str(300 * size)
        options = {"xvfb": "", 'quiet': '', 'format': 'jpeg', 'crop-h': dimensions, 'crop-w': dimensions}
        formatted_html = self.chart_html_flex.format(dimension=dimensions, arts=arts).format(*chart)

        imgkit.from_string(formatted_html, "downloads/fmchart.jpeg", options=options,
                           css='html/fm_chart_style.css')
        with open("downloads/fmchart.jpeg", "rb") as img:
            timer_upload = t.time()
            await ctx.send(f"{ctx.message.author.mention} `{period} {size}x{size}{chart_type} chart`", file=discord.File(img))
        if debug == "debug":
            await ctx.send(f"\nChart gen = {timer_upload - timer_start:.4f}s"
                           f"\nChart upload = {t.time() - timer_upload:.4f}s"
                           f"\nTotal = {t.time() - timer_start:.4f}s```")

    @commands.command()
    async def fmartist(self, ctx, *args):
        """Get your most listened tracks for an artist"""
        if len(args) == 0:
            await ctx.send("ERROR: Parameter `artist` is missing")
            return
        artist = " ".join(args)
        users_json = load_data()
        try:
            user = users_json["users"][str(ctx.message.author.id)]['lastfm_username']
        except Exception:
            await ctx.send("No username found in database, please use >fm set {username}")
            return
        track_limit = int(api_request({"method": "user.gettoptracks", "user": user})['toptracks']['@attr']['total'])
        tracks = []
        i = 1
        async with ctx.typing():
            for x in range(track_limit // 5000):
                tracks += api_request({"method": "user.gettoptracks", "user": user, "limit": track_limit, "page": i})['toptracks']['track']
                track_limit -= 5000
                i += 1
            tracks += api_request({"method": "user.gettoptracks", "user": user, "limit": track_limit, "page": i})['toptracks']['track']
            artists = {}
            for i in range(track_limit):
                this_artist = tracks[i]['artist']['name']
                if artist is not None:
                    if not this_artist.casefold() == artist.casefold():
                        continue
                    elif not artists:
                        artist_stylized = this_artist
                this_song = tracks[i]['name']
                this_playcount = tracks[i]['playcount']
                if this_artist not in artists:
                    artists[this_artist] = {}
                artists[this_artist][this_song] = this_playcount

        # await ctx.send(f"```json\n{json.dumps(artists, indent=4)}```")
        if artists:
            content = discord.Embed()
            content.title = f"{user}'s top tracks for {artist_stylized}"
            additional_songs = 0
            content.description = ""
            full = False
            for song in artists[artist_stylized]:
                if full:
                    additional_songs += 1
                else:
                    line = f"**{artists[artist_stylized][song]}** plays - **{song}**\n"
                    if len(content.description) + len(line) < 2000:
                        content.description += line
                    else:
                        full = True
            if full:
                content.set_footer(text=f"+ {additional_songs} more songs")
            await ctx.send(embed=content)
        else:
            await ctx.send("You haven't listened to this artist!")


def api_request(data_dict):
    """Get json data from lastfm api and return it
    :return json or None"""
    url = f"http://ws.audioscrobbler.com/2.0/?api_key={LASTFM_APPID}&format=json"
    for parameter in data_dict:
        url += f"&{parameter}={data_dict[parameter]}"
    response = requests.get(url)
    if response.status_code == 200:
        fm_data = json.loads(response.content.decode('utf-8'))
        return fm_data
    else:
        return None


def create_pages(rows):
    pages = []
    description = ""
    thisrow = 0
    for row in rows:
        thisrow += 1
        if len(description) + len(row) < 2000 and thisrow < 16:
            description += f"\n{row}"
        else:
            thisrow = 0
            pages.append(f"{description}")
            description = ""
    if not description == "":
        pages.append(f"{description}")
    return pages


def get_period(timeframe):
    if timeframe in ["7", "7day", "7days", "weekly", "week", "1week"]:
        period = "7day"
    elif timeframe in ["30", "30day", "30days", "monthly", "month", "1month"]:
        period = "1month"
    elif timeframe in ["90", "90day", "90days", "3months", "3month"]:
        period = "3month"
    elif timeframe in ["180", "180day", "180days", "6months", "6month", "halfyear"]:
        period = "6month"
    elif timeframe in ["365", "365day", "365days", "1year", "year", "yr", "12months", "12month", "yearly"]:
        period = "12month"
    elif timeframe in ["all", "at", "alltime", "forever", "overall"]:
        period = "overall"
    else:
        period = "overall"

    return period


def escape(string, amount):
    """escape asterisks to not mess with markdown"""
    if amount == 3:
        return string.replace("*", "*** \\****")
    else:
        return string.replace("*", "\\*")


def setup(client):
    client.add_cog(LastFM(client))

