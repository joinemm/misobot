from discord.ext import commands
import requests
import json
import discord
from datetime import datetime
from utils import logger as misolog
from utils import misc as misomisc
import imgkit
import time as t
import os
import cogs.utility as util
import main
import asyncio
from concurrent.futures import ThreadPoolExecutor

keys = os.environ
LASTFM_APPID = keys['LASTFM_APIKEY']
LASTFM_TOKEN = keys['LASTFM_SECRET']

database = main.database


class LastFM(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.logger = misolog.create_logger(__name__)
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

            database.set_attr("users", f"{ctx.author.id}.lastfm_username", timeframe)
            await ctx.send(f"{ctx.message.author.mention} Username saved as {timeframe}", embed=content)
            return
        else:
            username = database.get_attr("users", f"{ctx.author.id}.lastfm_username")
            if username is None:
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
            # noinspection PyBroadException
            try:
                amount = int(args[-1])
            except Exception:
                try:
                    amount = int(timeframe)
                except (TypeError, ValueError):
                    pass

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
                content.set_footer(text=f"page 1 of {len(pages)}")
            my_msg = await ctx.send(embed=content)

            if len(pages) > 1:
                await util.page_switcher(self.client, my_msg, content, pages)

    def userinfo(self, ctx, username):
        data = api_request({"user": username, "method": "user.getinfo"})
        if data is not None and "error" not in data:
            username = data['user']['name']
            playcount = data['user']['playcount']
            profile_url = data['user']['url']
            profile_pic_url = data['user']['image'][3]['#text']
            timestamp = int(data['user']['registered']['unixtime'])
            utc_time = datetime.utcfromtimestamp(timestamp)
            time = utc_time.strftime("%d/%m/%Y")

            image_colour = misomisc.get_color(profile_pic_url)
            content = discord.Embed()
            if image_colour is not None:
                content.colour = int(image_colour, 16)
            else:
                content.colour = discord.Color.magenta()
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
        if data is not None and "error" not in data:
            user_attr = data['recenttracks']['@attr']
            tracks = data['recenttracks']['track']
            artist = escape(tracks[0]['artist']['#text'], 2)
            album = escape(tracks[0]['album']['#text'], 2)
            track = escape(tracks[0]['name'], 2)
            image_url = tracks[0]['image'][-1]['#text']
            image_colour = misomisc.get_color(image_url)
            content = discord.Embed()
            if image_colour is not None:
                content.colour = int(image_colour, 16)
            else:
                content.colour = discord.Color.magenta()
            content.description = f"**{album}**"
            content.title = f"**{artist}** — ***{track}***"
            content.set_thumbnail(url=image_url)

            trackdata = api_request({"user": username, "method": "track.getInfo", "artist": artist, "track": track})
            if trackdata is not None:
                tags = []
                try:
                    trackdata = trackdata['track']
                    playcount = trackdata['userplaycount']
                    content.description = f"**{album}**\n{playcount} total plays"
                    for tag in trackdata['toptags']['tag']:
                        tags.append(tag['name'])
                except KeyError:
                    pass

                if tags:
                    content.set_footer(text=", ".join(tags))

            state = "Most recent track"
            if '@attr' in tracks[0]:
                if "nowplaying" in tracks[0]['@attr']:
                    state = "Now Playing"

            content.set_author(name=f"{user_attr['user']} — {state}",
                               icon_url=ctx.message.author.avatar_url)
            return content
        else:
            print(data)
            return None

    def recent_tracks(self, ctx, username, amount):
        if amount > 200:
            amount = 200
        data = api_request({"user": username, "method": "user.getrecenttracks", "limit": amount})
        if data is not None and "error" not in data:
            user_attr = data['recenttracks']['@attr']
            tracks = data['recenttracks']['track']
            description = []
            for i in range(amount):
                try:
                    artist = escape(tracks[i]['artist']['#text'], 2)
                    name = escape(tracks[i]['name'], 3)
                    description.append(f"**{artist}** — ***{name}***")
                except IndexError:
                    break
            image_url = tracks[0]['image'][-1]['#text']
            image_colour = misomisc.get_color(image_url)
            content = discord.Embed()
            if image_colour is not None:
                content.colour = int(image_colour, 16)
            else:
                content.colour = discord.Color.magenta()
            content.set_thumbnail(url=image_url)
            content.set_footer(text=f"Total plays: {user_attr['total']}")
            content.set_author(name=f"{user_attr['user']} — {amount} Recent tracks",
                               icon_url=ctx.message.author.avatar_url)

            pages = util.create_pages(description)
            content.description = pages[0]
            return content, pages
        else:
            print(data)
            return None

    def top_artists(self, ctx, username, period, amount):
        data = api_request({"user": username, "method": "user.gettopartists", "limit": amount, "period": period})
        if data is not None and "error" not in data:
            user_attr = data['topartists']['@attr']
            artists = data['topartists']['artist']
            description = []
            for i in range(amount):
                try:
                    artist = escape(artists[i]['name'], 2)
                    plays = artists[i]['playcount']
                    description.append(f"**{plays}** plays — **{artist}**")
                except IndexError:
                    break
            image_url = artists[0]['image'][-1]['#text']
            image_colour = misomisc.get_color(image_url)
            content = discord.Embed()
            if image_colour is not None:
                content.colour = int(image_colour, 16)
            else:
                content.colour = discord.Color.magenta()
            content.set_thumbnail(url=image_url)
            content.set_footer(text=f"Total unique artists: {user_attr['total']}")
            content.set_author(name=f"{user_attr['user']} — {amount} Most played artists {period}",
                               icon_url=ctx.message.author.avatar_url)
            pages = util.create_pages(description)
            content.description = pages[0]
            return content, pages
        else:
            print(data)
            return None

    def top_albums(self, ctx, username, period, amount):
        data = api_request({"user": username, "method": "user.gettopalbums", "limit": amount, "period": period})
        if data is not None and "error" not in data:
            user_attr = data['topalbums']['@attr']
            albums = data['topalbums']['album']
            description = []
            for i in range(amount):
                try:
                    album = escape(albums[i]['name'], 3)
                    artist = escape(albums[i]['artist']['name'], 2)
                    plays = albums[i]['playcount']
                    description.append(f"**{plays}** plays - ***{album}*** — **{artist}**")
                except IndexError:
                    break
            image_url = albums[0]['image'][-1]['#text']
            image_colour = misomisc.get_color(image_url)
            content = discord.Embed()
            if image_colour is not None:
                content.colour = int(image_colour, 16)
            else:
                content.colour = discord.Color.magenta()
            content.description = description
            content.set_thumbnail(url=image_url)
            content.set_footer(text=f"Total unique albums: {user_attr['total']}")
            content.set_author(name=f"{user_attr['user']} — {amount} Most played albums {period}",
                               icon_url=ctx.message.author.avatar_url)
            pages = util.create_pages(description)
            content.description = pages[0]
            return content, pages
        else:
            print(data)
            return None

    def top_tracks(self, ctx, username, period, amount):
        data = api_request({"user": username, "method": "user.gettoptracks", "limit": amount, "period": period})
        if data is not None and "error" not in data:
            user_attr = data['toptracks']['@attr']
            tracks = data['toptracks']['track']
            description = []
            for i in range(amount):
                try:
                    artist = escape(tracks[i]['artist']['name'], 2)
                    name = escape(tracks[i]['name'], 3)
                    plays = tracks[i]['playcount']
                    description.append(f"**{plays}** plays - **{artist}** — ***{name}***")
                except IndexError:
                    break
            image_url = tracks[0]['image'][-1]['#text']
            image_colour = misomisc.get_color(image_url)
            content = discord.Embed()
            if image_colour is not None:
                content.colour = int(image_colour, 16)
            else:
                content.colour = discord.Color.magenta()
            content.description = description
            content.set_thumbnail(url=image_url)
            content.set_footer(text=f"Total unique tracks: {user_attr['total']}")
            content.set_author(name=f"{user_attr['user']} — {amount} Most played tracks {period}",
                               icon_url=ctx.message.author.avatar_url)
            pages = util.create_pages(description)
            content.description = pages[0]
            return content, pages
        else:
            print(data)
            return None

    @commands.command()
    async def fmchart(self, ctx, *args):
        """Generate a chart from your lastfm stats"""
        self.logger.info(misolog.format_log(ctx, f""))
        timer_start = t.time()
        await ctx.message.channel.trigger_typing()

        username = database.get_attr("users", f"{ctx.author.id}.lastfm_username")
        if username is None:
            await ctx.send("No username found in database, please use >fm set [username]")
            return

        method = "topalbums"
        timeframe = "week"
        size = "3x3"

        args = list(args)
        for argument in args:
            if "x" in argument:
                size = argument
                args.remove(argument)
                break

        try:
            if args[0] in ["recent", "recents", "re", "topartists", "ta", "artist", "artists",
                           "topalbums", "talb", "albums", "album"]:
                method = args[0]
            else:
                timeframe = args[0]
            try:
                timeframe = args[1]
            except IndexError:
                pass
        except IndexError:
            pass

        period = get_period(timeframe)
        try:
            size = int(size.split("x")[0])
        except ValueError:
            await ctx.send(f"Error: invalid size `{size}`")
        if size > 14:
            await ctx.send("Error: Maximum supported chart size is `14x14`")
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

        elif method in ["topartists", "ta", "artist", "artists"]:
            data = api_request({"user": username, "method": "user.gettopartists",
                                "limit": (size * size), "period": period})
            chart_type = " Artist"
            artists = data['topartists']['artist']
            for i in range(len(chart)):
                try:
                    artist = artists[i]['name']
                    plays = artists[i]['playcount']
                    chart[i] = (f"{plays} plays<br>{artist}", artists[i]['image'][3]['#text'])
                except IndexError:
                    break

        elif method in ["topalbums", "talb", "albums", "album"]:
            data = api_request({"user": username, "method": "user.gettopalbums",
                                "limit": (size * size), "period": period})
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
            await ctx.send(f"`{ctx.message.author.name} {period} {size}x{size}{chart_type} chart`",
                           file=discord.File(img))
        if "debug" in args:
            await ctx.send(f"\nChart gen = {timer_upload - timer_start:.4f}s"
                           f"\nChart upload = {t.time() - timer_upload:.4f}s"
                           f"\nTotal = {t.time() - timer_start:.4f}s```")

    @commands.command()
    async def fmartist(self, ctx, mode, *args):
        """Get your most listened tracks or albums for an artist"""
        self.logger.info(misolog.format_log(ctx, f""))
        perpage = 200

        if mode in ["toptracks", "tt", "tracks", "track"]:
            method = "user.gettoptracks"
            json_attr = ["toptracks", "track"]
        elif mode in ["topalbums", "talb", "albums", "album"]:
            method = "user.gettopalbums"
            json_attr = ["topalbums", "album"]
        else:
            await ctx.send(f"ERROR: Invalid mode `{mode}`\ntry `topalbums` or `toptracks`")
            return

        if len(args) == 0:
            await ctx.send("ERROR: Parameter `artist` is missing\nusage: `>fmartist [tracks | albums] [artist name]`")
            return
        artist = " ".join(args)
        user = database.get_attr("users", f"{ctx.author.id}.lastfm_username")
        if user is None:
            await ctx.send("No username found in database, please use >fm set [username]")
            return

        async with ctx.typing():
            items = []
            data = api_request({"method": method, "user": user, "limit": perpage})
            total_pages = int(data[json_attr[0]]['@attr']['totalPages'])
            items += data[json_attr[0]][json_attr[1]]
            if total_pages > 1:
                loop = self.client.loop
                # future = asyncio.ensure_future(self.get_data(method, user, total_pages, perpage))
                # gather = loop.create_task(future)
                gather = await loop.create_task(self.fmartist_data_threaded(method, user, total_pages, perpage))
                for x in gather:
                    items += x[json_attr[0]][json_attr[1]]

            artist_data = {}
            formatted_name = None
        total_items = len(items)
        for i in range(total_items):
            this_artist = items[i]['artist']['name']
            if not this_artist.casefold() == artist.casefold():
                continue
            if formatted_name is None:
                formatted_name = this_artist
            this_item = items[i]['name']
            this_playcount = int(items[i]['playcount'])
            artist_data[this_item] = this_playcount

        if artist_data:
            artist_info = api_request({"method": "artist.getinfo", "artist": formatted_name})['artist']
            image_url = artist_info['image'][-1]['#text']

            content = discord.Embed()
            content.set_thumbnail(url=image_url)

            image_colour = misomisc.get_color(image_url)
            if image_colour is not None:
                content.colour = int(image_colour, 16)

            description = []
            total_plays = 0
            for i, item in enumerate(artist_data):
                line = f"`{i + 1}`. **{artist_data[item]}** plays - **{item}**"
                total_plays += artist_data[item]
                description.append(line)

            content.title = f"{user}'s top " + ("tracks" if method == "user.gettoptracks" else "albums") \
                            + f" for {formatted_name} | Total {total_plays} plays"
            pages = util.create_pages(description)
            content.description = pages[0]

            if len(pages) > 1:
                content.set_footer(text=f"page 1 of {len(pages)}")
            my_msg = await ctx.send(embed=content)

            if len(pages) > 1:
                await util.page_switcher(self.client, my_msg, content, pages)

        else:
            await ctx.send("You haven't listened to this artist! "
                           "Make sure the artist name is formatted exactly as it shows up in the last fm database.")

    async def fmartist_data_threaded(self, method, user, total_pages, perpage):
        with ThreadPoolExecutor(max_workers=20) as executor:
            loop = asyncio.get_event_loop()
            datas = [{"method": method, "user": user, "limit": perpage, "page": i} for i in range(2, total_pages + 1)]
            tasks = [
                loop.run_in_executor(
                    executor,
                    api_request,
                    data
                )
                for data in datas
            ]
            return await asyncio.gather(*tasks)

    @commands.command()
    async def whoknows(self, ctx, *args):
        artistname = " ".join(args)
        await ctx.message.channel.trigger_typing()
        listeners = []
        for userid in database.get_attr("users", "."):
            lastfm_username = database.get_attr("users", f"{userid}.lastfm_username")
            if lastfm_username is None:
                continue

            member = ctx.guild.get_member(int(userid))
            # member = self.client.get_user(int(userid))
            if member is None:
                continue

            # is on this server and has lastfm connected
            playcount = get_playcount(artistname, lastfm_username)
            if playcount > 0:
                listeners.append((playcount, member))

        rows = []
        for i, x in enumerate(sorted(listeners, key=lambda p: p[0], reverse=True)):
            if i == 0:
                rank = ":crown:"
            else:
                rank = f"`{i + 1}`."
            rows.append(f"{rank} **{x[1].name}** - **{x[0]}** plays")

        content = discord.Embed(title=f"Who knows **{artistname}**?")
        if not rows:
            return await ctx.send(f"Nobody on this server has listened to **{artistname}**")

        pages = util.create_pages(rows)
        content.description = pages[0]

        if len(pages) > 1:
            content.set_footer(text=f"page 1 of {len(pages)}")
        my_msg = await ctx.send(embed=content)

        if len(pages) > 1:
            await util.page_switcher(self.client, my_msg, content, pages)


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
        print(f"Api request error code {response.status_code}, returning None")
        print(json.loads(response.content.decode('utf-8')))
        return None


def get_playcount(artist, username):
    data = api_request({"method": "artist.getinfo", "user": username, "artist": artist})
    try:
        return int(data['artist']['stats']['userplaycount'])
    except KeyError:
        return 0


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
