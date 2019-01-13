import requests
from colorthief import ColorThief
import math


def get_color(url):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open('album_art.png', 'wb') as f:
            for chunk in r:
                f.write(chunk)
    else:
        return "ffffff"

    color_thief = ColorThief('album_art.png')
    dominant_color = color_thief.get_color(quality=100)

    return to_hex(dominant_color)


def to_hex(rgb):
    r, g, b = rgb

    def clamp(x):
        return max(0, min(x, 255))

    return "{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))


def get_xp(level):
        a = 0
        for x in range(1, level):
            a += math.floor(x + 300 * math.pow(2, (x / 7)))
        return math.floor(a / 4)


def get_level(xp):
    i = 1
    while get_xp(i+1) < xp:
        i += 1
    return i


def xp_to_next_level(level):
    return get_xp(level + 1) - get_xp(level)


def xp_from_message(message):
    xp = len(message.content.split(" ")) + 10 * len(message.attachments)
    return xp