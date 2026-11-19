"""Renderiza o calendário de contribuições retornado pela API GraphQL do GitHub."""
import json
import math
import random
import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "atlas"
MONTHS = "JAN FEV MAR ABR MAI JUN JUL AGO SET OUT NOV DEZ".split()
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


def label(draw, xy, text, size, color, family="DejaVuSansMono"):
    font = ImageFont.truetype(str(FONT_DIR / f"{family}.ttf"), size)
    draw.text(xy, text, font=font, fill=color, anchor="lt")


def star(draw, x, y, r, color):
    draw.polygon([(x, y-r), (x+1, y-1), (x+r, y), (x+1, y+1),
                  (x, y+r), (x-1, y+1), (x-r, y), (x-1, y-1)], fill=color)


def month_label(day):
    return f"{MONTHS[day.month - 1]} {day.year}"


def render(calendar):
    weeks = calendar["weeks"]
    days = [day for week in weeks for day in week["contributionDays"]]
    total = calendar["totalContributions"]
    if not days or sum(day["contributionCount"] for day in days) != total:
        raise ValueError("Calendário incompleto ou incompatível com o total da API")

    first = date.fromisoformat(days[0]["date"])
    last = date.fromisoformat(days[-1]["date"])
    image = Image.new("RGB", (1000, 238), "#081027")
    draw = ImageDraw.Draw(image)
    rng = random.Random(42)
    for _ in range(183):
        draw.point((rng.randrange(1000), rng.randrange(238)), fill="#456489")
    star(draw, 28, 27, 8, "#347aff")
    label(draw, (48, 20), "TELEMETRIA", 14, "#9ad6ff")
    label(draw, (810, 20), "ATIVIDADE NO GITHUB", 14, "#aac2df")
    draw.line((24, 48, 976, 48), fill="#294366")
    label(draw, (28, 76), str(total), 61, "#f1f6ff", "DejaVuSansCondensed-Bold")
    label(draw, (30, 151), "contribuições", 20, "#9ad6ff", "DejaVuSans")
    label(draw, (30, 194), f"{month_label(first)} — {month_label(last)}", 14, "#aac2df")

    for week_index, week in enumerate(weeks):
        for day in week["contributionDays"]:
            weekday = day["weekday"]  # A API usa domingo como dia zero.
            x = 295 + 12 * week_index - 6 * weekday
            y = 109 + 0.8 * week_index + 6 * weekday
            count = day["contributionCount"]
            top = y - min(82, round(math.log2(1 + count) * 12))
            color = "#203957"
            if count:
                color = "#71c8ff" if count > 4 else "#338aff"
                draw.polygon([(x-6, top+5), (x+5, top+6), (x+5, y+6), (x-6, y+5)], fill="#1749b0")
                draw.polygon([(x+5, top+6), (x+11, top+1), (x+11, y+1), (x+5, y+6)], fill="#296ce9")
            draw.polygon([(x, top), (x+11, top+1), (x+5, top+6), (x-6, top+5)], fill=color)

    frames = []
    for index in range(54):
        frame = image.copy()
        draw = ImageDraw.Draw(frame)
        x = 268 + index * 13
        for offset in range(20):
            tail = x - offset * 2
            if 269 < tail < 944:
                draw.point((tail, 74 + 12 * math.sin(tail / 124)),
                           fill=(112 - offset * 4, 205 - offset * 6, 255 - offset * 6))
        if 269 < x < 944:
            star(draw, x, 74 + 12 * math.sin(x / 124), 3, "#f1f6ff")
        frames.append(frame)
    image.save(OUTPUT / "telemetria.png", optimize=True)
    frames[0].save(OUTPUT / "telemetria.gif", save_all=True, append_images=frames[1:],
                   duration=105, loop=0, optimize=True)
    print(f"{total} contribuições até {last.isoformat()}")


if __name__ == "__main__":
    response = json.load(sys.stdin)
    if response.get("errors"):
        raise ValueError("A consulta GraphQL retornou erros")
    render(response["data"]["user"]["contributionsCollection"]["contributionCalendar"])
