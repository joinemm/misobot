from discord.ext import commands
import requests
from lxml import html
import json
from fake_useragent import UserAgent
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import random as rd

proxies = []  # Will contain proxies [ip, port]
ua = UserAgent()


class Nsfw:

    def __init__(self, client):
        self.client = client

    @commands.command(hidden=True)
    async def nsfw(self, ctx):
        print(f"{ctx.message.author} >nsfw")
        channel_nsfw = ctx.channel.is_nsfw()
        if channel_nsfw:
            await ctx.send("current channel is nsfw")
        else:
            await ctx.send("current channel is NOT nsfw")

    @commands.command(hidden=True)
    async def phub_json(self, ctx, *args):
        print(f"{ctx.message.author} >phub_json {args}")
        channel_nsfw = ctx.channel.is_nsfw()
        if channel_nsfw:
            try:
                amount = int(args[len(args)-1])
                string = " ".join(args[:len(args) - 1])
            except ValueError:
                amount = 1
                string = " ".join(args)
            print("searching pornhub with keyword: " + string)
            while True:
                try:
                    json_data = scrape_ph(string, amount)
                    break
                except Exception as error:
                    print("error in while loop;" + str(error))

            await ctx.send("```json\n" + json.dumps(json_data, indent=4) + "\n```")
            print("successful send")
        else:
            print("Error: not nsfw channel")
            await ctx.send("Please go to an NSFW channel to use this command :flushed:")

    @commands.command(hidden=True)
    async def phub(self, ctx, *args):
        print(f"{ctx.message.author} >phub {args}")
        channel_nsfw = ctx.channel.is_nsfw()
        if channel_nsfw:
            video_url = "https://www.pornhub.com/view_video.php?viewkey="
            amount = 1
            string = " ".join(args)
            print("searching pornhub with keyword: " + string)
            while True:
                try:
                    json_data, status_code = scrape_ph(string, amount)
                    print(status_code)
                    print(json_data)
                    break
                except Exception as error:
                    print(error)

            vkey = json_data["videos"][0]["vkey"]
            await ctx.send(video_url + vkey)
            print("successful send")
        else:
            print("Error: not NSFW channel")
            await ctx.send("Please go to an NSFW channel to use this command :flushed:")


def scrape_ph(string, amount_to_return):
    new_proxy = proxy()
    proxy_dict = {
        "http": f"http://{new_proxy['ip']}:{new_proxy['port']}",
        "https": f"https://{new_proxy['ip']}:{new_proxy['port']}",
        "ftp": f"ftp://{new_proxy['ip']}:{new_proxy['port']}"
    }
    ph_data = {"videos": [], }
    url = 'https://www.pornhub.com/video/search?search=' + string
    page = requests.get(url, proxies=proxy_dict)
    tree = html.fromstring(page.content)
    results = tree.xpath('//ul[@id="videoSearchResult"]/li[@class=" js-pop videoblock videoBox"]')
    results_views = tree.xpath('//ul[@id="videoSearchResult"]/li[@class=" js-pop videoblock videoBox"]'
                               '/div/div/span[@class="views"]/var/text()')
    results_title = tree.xpath('//ul[@id="videoSearchResult"]/li[@class=" js-pop videoblock videoBox"]'
                               '/div/div/span[@class="title"]/a')
    results_rating = tree.xpath('//ul[@id="videoSearchResult"]/li[@class=" js-pop videoblock videoBox"]'
                                '/div/div/div[@class="rating-container up"]/div[@class="value"]/text()')

    print(results)
    print(results_views)
    print(results_title)
    print(results_rating)
    for i in range(amount_to_return):
        ph_data["videos"].append({"title": results_title[i].attrib["title"],
                                  "vkey": results[i].attrib["_vkey"],
                                  "views": results_views[i],
                                  "rating": results_rating[i]})
    print(ph_data)
    return ph_data, page.status_code


def proxy():
    # Retrieve latest proxies
    proxies_req = Request('https://www.sslproxies.org/')
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urlopen(proxies_req).read().decode('utf8')

    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    # Save proxies in the array
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({
            'ip': row.find_all('td')[0].string,
            'port': row.find_all('td')[1].string
        })

    # Choose a random proxy
    proxy_index = random_proxy()
    print(proxies[proxy_index])
    return proxies[proxy_index]


def random_proxy():
    return rd.randint(0, len(proxies) - 1)


def setup(client):
    client.add_cog(Nsfw(client))
