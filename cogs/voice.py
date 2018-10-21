import asyncio
import requests
import discord
import youtube_dl
import re
from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdlopts)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        info = ytdl.extract_info(url)
        return discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(filename, **ffmpeg_options)), info


class Voice:
    def __init__(self, client):
        self.client = client
        self.queue = []

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        print(f"{ctx.message.author} >join {channel}")
        """Joins a voice channel"""
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()

    @commands.command()
    async def play(self, ctx, *args):
        print(f"{ctx.message.author} >play {args}")
        search_string = " ".join(args)
        response = requests.get('http://www.youtube.com/results?search_query=' + search_string)
        if response.status_code == 200:
            search_results = re.findall('href=\\"\\/watch\\?v=(.{11})', response.content.decode())
            url = 'http://www.youtube.com/watch?v=' + search_results[0]
        else:
            await ctx.send("Error: status code " + str(response.status_code))
            return
        self.queue.append(url)

        async with ctx.typing():
            player, info = await YTDLSource.from_url(self.queue.pop(0), loop=self.client.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
            length = info.get('duration', None)
            title = info.get('title', None)
        await ctx.send(f"Now playing: **{title}** - Duration: **{length//60}:{str(int(length%60.)).zfill(2)}**")

    @commands.command()
    async def stop(self, ctx):
        print(f"{ctx.message.author} >stop")
        """Stops and disconnects the bot from voice"""
        await ctx.voice_client.disconnect()

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


def setup(client):
    client.add_cog(Voice(client))
