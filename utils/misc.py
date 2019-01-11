import requests
from colorthief import ColorThief


def get_color(url):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open('testimg.png', 'wb') as f:
            for chunk in r:
                f.write(chunk)

    color_thief = ColorThief('testimg.png')

    # get the dominant color
    dominant_color = color_thief.get_color(quality=1)
    return to_hex(dominant_color)


def to_hex(rgb):
    r, g, b = rgb

    def clamp(x):
        return max(0, min(x, 255))

    return "{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))