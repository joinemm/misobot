import discord
from discord.ext import commands
import re
import tweepy
from tweepy import OAuthHandler
import json
import os

keys = os.environ
TWITTER_CKEY = keys['TWITTER_CKEY']
TWITTER_CSECRET = keys['TWITTER_CSECRET']

auth = OAuthHandler(TWITTER_CKEY, TWITTER_CSECRET)
twt = tweepy.API(auth)


class Webhook:

    def __init__(self, client):
        self.client = client

    async def on_message(self, message):

        if message.channel.id in [523705582260322304] and message.content.startswith('embed'):
            channel = message.channel
            tweet_id = re.search(r'status/(\d+)', message.content).group(1)
            tweet = twt.get_status(tweet_id, tweet_mode='extended')

            media_files = []
            try:
                media = tweet.extended_entities.get('media', [])
            except AttributeError:
                print("No media found in webhook tweet, skipping.")
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

                await channel.send(embed=content)

                if file[2] is not None:
                    # content.description = f"Contains video/gif [Click here to view]({file[2]})"
                    await channel.send(file[2])

            await message.delete()


def setup(client):
    client.add_cog(Webhook(client))
