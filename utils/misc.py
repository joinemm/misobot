import requests
from colorthief import ColorThief
import math

blocks = [" ", ".", ":", "|"]


def get_color(url):
    try:
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
    except Exception as e:
        print(e)
        return None


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
    while get_xp(i + 1) < xp:
        i += 1
    return i


def xp_to_next_level(level):
    return get_xp(level + 1) - get_xp(level)


def xp_from_message(message):
    xp = len(message.content.split(" ")) + 10 * len(message.attachments)
    return xp


def cap(data, floor, height, steps):
    highest = max(data)
    if highest < floor:
        highest = floor

    piece = (highest / steps) / height

    new_list = []
    for i in range(len(data)):
        new_item = round(data[i] / piece)
        new_list.append(new_item)
    return new_list


def generate_graph(data, height, floor=100):
    steps = len(blocks) - 1
    data = cap(data, floor, height, steps)
    nums = [str(i).zfill(2) for i in range(len(data))]
    rows = []
    for row in reversed(range(height)):
        this_row = ""
        for i in range(len(data)):
            rem = data[i] - (row * steps)
            if rem < 0:
                rem = 0
            elif rem > steps:
                rem = steps
            this_row += blocks[rem]
        rows.append(this_row)

    number_row = []
    for z in range(2):
        this_row = ""
        for number in nums:
            this_row += number[z]
        number_row.append(this_row)

    return rows, number_row
