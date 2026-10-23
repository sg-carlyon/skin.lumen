"""Render Lumen's dashboard tiles (from the 4K mockup's SVGs) to PNGs with headless Edge,
and generate the supporting textures (rounded mask, focus ring, shadow) with Pillow.

Usage: python make_tiles.py <skin media/lumen folder> <work folder>
"""
import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

OUT = pathlib.Path(sys.argv[1])
WORK = pathlib.Path(sys.argv[2])
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
W, H, R = 1056, 594, 80  # 2x the 528x297 tile; radius 80 = 20 at 1080p skin coords

FONT = "Inter, sans-serif"
TILES = {
    "pov": ("#08080f", f'''<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2ee6ff"/><stop offset="1" stop-color="#e040fb"/></linearGradient></defs>
<circle cx="470" cy="40" r="190" fill="#14142c"/>
<text x="280" y="205" text-anchor="middle" font-family="{FONT}" font-weight="900" font-style="italic" font-size="150" letter-spacing="-4" fill="url(#g)">POV</text>'''),
    "umbrella": ("#2a0d10", '''<circle cx="90" cy="300" r="200" fill="#36131a"/>
<polygon points="140,157 206,157 186.7,203.7" fill="#c3141e"/><polygon points="140,157 186.7,203.7 140,223" fill="#f1eeee"/>
<polygon points="140,157 140,223 93.3,203.7" fill="#c3141e"/><polygon points="140,157 93.3,203.7 74,157" fill="#f1eeee"/>
<polygon points="140,157 74,157 93.3,110.3" fill="#c3141e"/><polygon points="140,157 93.3,110.3 140,91" fill="#f1eeee"/>
<polygon points="140,157 140,91 186.7,110.3" fill="#c3141e"/><polygon points="140,157 186.7,110.3 206,157" fill="#f1eeee"/>''' +
        f'<text x="236" y="178" font-family="{FONT}" font-weight="700" font-size="60" letter-spacing="-1" fill="#f4eeee">Umbrella</text>'),
    "youtube": ("#0f0f0f", f'''<rect x="88" y="112" width="132" height="92" rx="26" fill="#ff0033"/><polygon points="140,136 140,180 180,158" fill="#fff"/>
<text x="238" y="180" font-family="{FONT}" font-weight="700" font-size="64" letter-spacing="-2.5" fill="#fff">YouTube</text>'''),
    "youtube-tv": ("#1b1b1b", f'''<rect x="0" y="230" width="560" height="85" fill="#232323"/>
<rect x="64" y="112" width="132" height="92" rx="26" fill="#ff0033"/><polygon points="116,136 116,180 156,158" fill="#fff"/>
<text x="210" y="178" font-family="{FONT}" font-weight="700" font-size="56" letter-spacing="-2" fill="#fff">YouTube</text>
<rect x="434" y="134" width="66" height="46" rx="10" fill="none" stroke="#fff" stroke-width="4"/>
<text x="467" y="167" text-anchor="middle" font-family="{FONT}" font-weight="800" font-size="28" fill="#fff">TV</text>'''),
    "livetv": ("#0d2f38", f'''<rect x="150" y="62" width="260" height="152" rx="18" fill="#0a1d23" stroke="#d9eef3" stroke-width="8"/>
<rect x="172" y="88" width="90" height="22" rx="5" fill="#2f7383"/><rect x="270" y="88" width="118" height="22" rx="5" fill="#2f7383"/>
<rect x="172" y="126" width="140" height="22" rx="5" fill="#2f7383"/><rect x="320" y="126" width="68" height="22" rx="5" fill="#2f7383"/>
<rect x="172" y="164" width="64" height="22" rx="5" fill="#2f7383"/><rect x="244" y="164" width="144" height="22" rx="5" fill="#2f7383"/>
<line x1="296" y1="76" x2="296" y2="200" stroke="#ff5a4e" stroke-width="6" stroke-linecap="round"/>
<line x1="250" y1="232" x2="310" y2="232" stroke="#d9eef3" stroke-width="8" stroke-linecap="round"/>
<text x="280" y="284" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="40" fill="#e6f4f7">Live TV</text>'''),
    "movies": ("#16223a", f'''<circle cx="500" cy="300" r="190" fill="#1c2b48"/>
<rect x="200" y="74" width="160" height="28" rx="6" fill="#f5c46b"/>
<polygon points="222,74 244,74 230,102 208,102" fill="#16223a"/><polygon points="266,74 288,74 274,102 252,102" fill="#16223a"/><polygon points="310,74 332,74 318,102 296,102" fill="#16223a"/>
<rect x="200" y="108" width="160" height="112" rx="12" fill="#e8eef8"/><polygon points="266,138 266,190 306,164" fill="#16223a"/>
<text x="280" y="280" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="40" fill="#e8eef8">Movies</text>'''),
    "tvshows": ("#173a2e", f'''<rect x="226" y="62" width="150" height="100" rx="12" fill="#2f6b55"/><rect x="208" y="80" width="164" height="110" rx="13" fill="#4d8f76"/>
<rect x="188" y="98" width="184" height="122" rx="14" fill="#e6f2ec"/><polygon points="262,132 262,186 306,159" fill="#173a2e"/>
<text x="280" y="280" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="40" fill="#e6f2ec">TV Shows</text>'''),
    "library": ("#1e2a44", f'''<circle cx="500" cy="300" r="190" fill="#24334f"/>
<rect x="196" y="70" width="44" height="150" rx="8" fill="#7fa3d6"/>
<rect x="248" y="70" width="44" height="150" rx="8" fill="#e8eef8"/>
<rect x="300" y="84" width="44" height="136" rx="8" fill="#f5c46b" transform="rotate(12 322 220)"/>
<line x1="186" y1="226" x2="374" y2="226" stroke="#e8eef8" stroke-width="8" stroke-linecap="round"/>
<text x="280" y="282" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="40" fill="#e8eef8">My Library</text>'''),
    "favourites": ("#33280f", f'''<circle cx="70" cy="300" r="190" fill="#3d3013"/>
<path d="M280 62 L304 118 L364 123 L318 162 L332 221 L280 190 L228 221 L242 162 L196 123 L256 118 Z" fill="#f5c46b" stroke="#f5c46b" stroke-width="8" stroke-linejoin="round"/>
<text x="280" y="282" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="40" fill="#f6ead0">Favourites</text>'''),
    "music": ("#34183a", f'''<circle cx="60" cy="40" r="170" fill="#401e47"/>
<polygon points="250,86 340,68 340,96 250,114" fill="#f0dcf4"/>
<line x1="256" y1="96" x2="256" y2="196" stroke="#f0dcf4" stroke-width="12"/><line x1="334" y1="80" x2="334" y2="180" stroke="#f0dcf4" stroke-width="12"/>
<ellipse cx="234" cy="198" rx="28" ry="21" fill="#f0dcf4"/><ellipse cx="312" cy="182" rx="28" ry="21" fill="#f0dcf4"/>
<text x="280" y="280" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="40" fill="#f0dcf4">Music</text>'''),
    "photos": ("#f3f1ec", f'''<g transform="translate(280 146)">
<ellipse cx="0" cy="-42" rx="30" ry="46" fill="#f24b3f" opacity="0.92"/>
<ellipse cx="0" cy="-42" rx="30" ry="46" fill="#ffb400" opacity="0.92" transform="rotate(72)"/>
<ellipse cx="0" cy="-42" rx="30" ry="46" fill="#18b45b" opacity="0.92" transform="rotate(144)"/>
<ellipse cx="0" cy="-42" rx="30" ry="46" fill="#1e83f7" opacity="0.92" transform="rotate(216)"/>
<ellipse cx="0" cy="-42" rx="30" ry="46" fill="#e46fb0" opacity="0.92" transform="rotate(288)"/></g>
<text x="280" y="284" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="40" fill="#1c1c1c">Photos</text>'''),
    "browser": ("#12304d", f'''<circle cx="280" cy="140" r="64" fill="none" stroke="#dbe8f5" stroke-width="9"/>
<ellipse cx="280" cy="140" rx="27" ry="64" fill="none" stroke="#dbe8f5" stroke-width="7"/>
<line x1="216" y1="140" x2="344" y2="140" stroke="#dbe8f5" stroke-width="7"/>
<path d="M226 108 Q280 122 334 108 M226 172 Q280 158 334 172" fill="none" stroke="#dbe8f5" stroke-width="6"/>
<text x="280" y="280" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="40" fill="#dbe8f5">Browser</text>'''),
    "settings": ("#22262d", '<g transform="translate(280 140)" fill="#e1e4e9">' +
        "".join(f'<rect x="-11" y="-76" width="22" height="26" rx="5" transform="rotate({a})"/>' for a in range(0, 360, 45)) +
        f'''<circle r="48" fill="none" stroke="#e1e4e9" stroke-width="18"/></g>
<text x="280" y="280" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="40" fill="#e1e4e9">Settings</text>'''),
    "power": ("#2a1a1a", f'''<line x1="280" y1="76" x2="280" y2="140" stroke="#ff8a73" stroke-width="16" stroke-linecap="round"/>
<path d="M236 102 A68 68 0 1 0 324 102" fill="none" stroke="#ff8a73" stroke-width="16" stroke-linecap="round"/>
<text x="280" y="284" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="40" fill="#f3dcd6">Power</text>'''),
}

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,700;0,800;1,900&display=block" rel="stylesheet">
<style>html,body{{margin:0;background:transparent}}div{{width:{w}px;height:{h}px;border-radius:{r}px;overflow:hidden;background:{bg}}}svg{{display:block}}</style>
</head><body><div><svg width="{w}" height="{h}" viewBox="0 0 560 315" xmlns="http://www.w3.org/2000/svg">{svg}</svg></div></body></html>"""


def rounded(size, radius, fill):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=fill)
    return img


def main():
    (OUT / "tiles").mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    for name, (bg, svg) in TILES.items():
        page = WORK / f"{name}.html"
        page.write_text(PAGE.format(w=W, h=H, r=R, bg=bg, svg=svg), encoding="utf-8")
        shot = WORK / f"{name}.png"
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={W},{H}",
                        "--default-background-color=00000000", "--virtual-time-budget=6000",
                        f"--screenshot={shot}", page.as_uri()], check=True, capture_output=True, timeout=120)
        tile = Image.open(shot).convert("RGBA").crop((0, 0, W, H))
        # Clean anti-aliased corners: apply our own rounded alpha mask.
        mask = rounded((W, H), R, (255, 255, 255, 255)).getchannel("A")
        tile.putalpha(Image.composite(tile.getchannel("A"), Image.new("L", (W, H), 0), mask))
        tile.save(OUT / "tiles" / f"{name}.png", optimize=True)
        print("tile", name)

    # Rounded mask for Up next stills (16:9), used as a Kodi diffuse texture.
    rounded((W, H), R, (255, 255, 255, 255)).save(OUT / "mask-16x9.png", optimize=True)
    # Focus ring: a 16 px white outline (4 px at 1080p) hugging the tile; it zooms with the tile.
    pad = 16
    ring_w, ring_h = W + 2 * pad, H + 2 * pad
    ring = rounded((ring_w, ring_h), R + pad, (255, 255, 255, 255))
    inner = rounded((ring_w - 2 * pad, ring_h - 2 * pad), R, (255, 255, 255, 255))
    hole = Image.new("RGBA", (ring_w, ring_h), (0, 0, 0, 0))
    hole.paste(inner, (pad, pad))
    ring.putalpha(Image.composite(Image.new("L", (ring_w, ring_h), 0), ring.getchannel("A"), hole.getchannel("A")))
    ring.save(OUT / "tile-focus.png", optimize=True)
    # Soft drop shadow behind the focused tile.
    sw, sh, blur = W + 240, H + 240, 48
    shadow = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    shadow.paste(rounded((W, H), R, (0, 0, 0, 200)), (120, 150))
    shadow.filter(ImageFilter.GaussianBlur(blur)).save(OUT / "tile-shadow.png", optimize=True)
    # App glow: a soft white radial falloff that the skin tints with each tile's colour.
    size = 512
    glow = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            d = min(1.0, ((x - c) ** 2 + (y - c) ** 2) ** 0.5 / c)
            glow.putpixel((x, y), (255, 255, 255, int(round(255 * (1 - d) ** 2.2))))
    glow.save(OUT / "glow.png", optimize=True)
    print("textures done")


if __name__ == "__main__":
    main()
