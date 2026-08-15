import argparse
import json
import math
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

PAGE = landscape((10 * inch, 5.625 * inch))
W, H = PAGE
MARGIN = 0.46 * inch

INK = colors.HexColor("#12151C")
MUTED = colors.HexColor("#596171")
PAPER = colors.HexColor("#F7F4EE")
LINE = colors.HexColor("#DDD7CB")
WHITE = colors.white

THEMES = [
    {
        "name": "blueprint",
        "accent": "#175CFF",
        "accent_2": "#28B6F6",
        "dark": "#111827",
        "warm": "#F4D35E",
    },
    {
        "name": "evergreen",
        "accent": "#087F5B",
        "accent_2": "#63D471",
        "dark": "#102A27",
        "warm": "#FFB703",
    },
    {
        "name": "signal",
        "accent": "#8F2DFF",
        "accent_2": "#FF5DA2",
        "dark": "#171321",
        "warm": "#FFD166",
    },
    {
        "name": "oxide",
        "accent": "#D9480F",
        "accent_2": "#F59F00",
        "dark": "#211816",
        "warm": "#9AE6B4",
    },
]


def hx(value):
    return colors.HexColor(value)


def theme_for(deck):
    seed = f"{deck.get('title', '')} {deck.get('subtitle', '')}".lower()
    score = sum(ord(ch) for ch in seed)
    return THEMES[score % len(THEMES)]


def clamp(text, n):
    text = str(text or "").strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "..."


def wrap(c, text, font, size, max_width):
    c.setFont(font, size)
    words = str(text or "").split()
    lines = []
    line = ""
    for word in words:
        trial = f"{line} {word}".strip()
        if c.stringWidth(trial, font, size) <= max_width:
            line = trial
            continue
        if line:
            lines.append(line)
        line = word
    if line:
        lines.append(line)
    return lines


def lerp(a, b, t):
    return a + (b - a) * t


def rgb(hex_color):
    value = hex_color.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def gradient(c, x, y, w, h, start, end, steps=80):
    sr, sg, sb = rgb(start)
    er, eg, eb = rgb(end)
    stripe = h / steps
    for i in range(steps):
        t = i / max(steps - 1, 1)
        c.setFillColor(
            colors.Color(lerp(sr, er, t) / 255, lerp(sg, eg, t) / 255, lerp(sb, eb, t) / 255)
        )
        c.rect(x, y + i * stripe, w, stripe + 1, fill=1, stroke=0)


def rounded(c, x, y, w, h, r=14, fill=WHITE, stroke=None, width=1):
    c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(width)
        c.roundRect(x, y, w, h, r, fill=1, stroke=1)
    else:
        c.roundRect(x, y, w, h, r, fill=1, stroke=0)


def footer(c, index, total, theme):
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(MARGIN, 0.25 * inch, "textshop")
    c.drawRightString(W - MARGIN, 0.25 * inch, f"{index:02d} / {total:02d}")
    c.setStrokeColor(hx(theme["accent"]))
    c.setLineWidth(1.2)
    c.line(MARGIN, 0.39 * inch, MARGIN + 0.8 * inch, 0.39 * inch)


def draw_title_block(c, title, subtitle, theme):
    c.setFillColor(WHITE)
    title_lines = wrap(c, title, "Helvetica-Bold", 43, W - 2 * MARGIN - 0.5 * inch)[:3]
    y = H - 1.35 * inch
    for line in title_lines:
        c.setFont("Helvetica-Bold", 43)
        c.drawString(MARGIN, y, line)
        y -= 0.52 * inch

    c.setFillColor(colors.Color(1, 1, 1, 0.82))
    c.setFont("Helvetica", 15)
    for line in wrap(c, subtitle, "Helvetica", 15, W - 2 * MARGIN - 1.4 * inch)[:3]:
        c.drawString(MARGIN, y - 0.08 * inch, line)
        y -= 0.25 * inch

    rounded(
        c,
        W - MARGIN - 1.8 * inch,
        H - MARGIN - 0.48 * inch,
        1.8 * inch,
        0.38 * inch,
        r=12,
        fill=colors.Color(1, 1, 1, 0.14),
        stroke=colors.Color(1, 1, 1, 0.22),
    )
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(WHITE)
    c.drawCentredString(W - MARGIN - 0.9 * inch, H - MARGIN - 0.33 * inch, "INVESTOR DECK")


def draw_big_number(c, value, label, x, y, w, theme):
    rounded(c, x, y, w, 0.76 * inch, r=14, fill=colors.Color(1, 1, 1, 0.14))
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 25)
    c.drawString(x + 0.16 * inch, y + 0.39 * inch, clamp(value, 12))
    c.setFillColor(colors.Color(1, 1, 1, 0.72))
    c.setFont("Helvetica", 8.5)
    c.drawString(x + 0.16 * inch, y + 0.18 * inch, clamp(label, 28).upper())


def title_slide(c, deck, theme):
    gradient(c, 0, 0, W, H, theme["dark"], theme["accent"])
    c.setFillColor(colors.Color(1, 1, 1, 0.07))
    for i in range(9):
        c.circle(W * (0.68 + i * 0.045), H * (0.2 + math.sin(i) * 0.07), 1.2 * inch, fill=1, stroke=0)

    title = deck.get("title") or "Pitch Deck"
    subtitle = deck.get("subtitle") or "A sharper story, built by TextShop."
    draw_title_block(c, title, subtitle, theme)

    metrics = deck.get("metrics") or [
        {"value": f"{len(deck.get('slides', []))}", "label": "slides"},
        {"value": "human", "label": "review included"},
        {"value": "sms", "label": "ordered by text"},
    ]
    x = MARGIN
    for metric in metrics[:3]:
        draw_big_number(
            c,
            str(metric.get("value", "")),
            str(metric.get("label", "")),
            x,
            MARGIN,
            1.72 * inch,
            theme,
        )
        x += 1.9 * inch
    c.showPage()


def slide_kicker(slide, index):
    return slide.get("kicker") or slide.get("type") or f"slide {index:02d}"


def draw_header(c, slide, index, total, theme):
    c.setFillColor(hx(theme["accent"]))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(MARGIN, H - MARGIN + 0.03 * inch, slide_kicker(slide, index).upper())

    c.setFillColor(INK)
    y = H - MARGIN - 0.33 * inch
    for line in wrap(c, slide.get("heading", ""), "Helvetica-Bold", 29, W - 2 * MARGIN)[:2]:
        c.setFont("Helvetica-Bold", 29)
        c.drawString(MARGIN, y, line)
        y -= 0.38 * inch
    footer(c, index, total, theme)
    return y - 0.08 * inch


def draw_bullet(c, x, y, text, theme, max_width, size=13.4):
    c.setFillColor(hx(theme["accent"]))
    c.circle(x + 0.04 * inch, y + 0.06 * inch, 3.2, fill=1, stroke=0)
    c.setFillColor(INK)
    lines = wrap(c, text, "Helvetica", size, max_width)
    for i, line in enumerate(lines[:3]):
        c.setFont("Helvetica", size)
        c.drawString(x + 0.18 * inch, y - i * 0.19 * inch, line)
    return y - max(1, len(lines[:3])) * 0.19 * inch - 0.13 * inch


def draw_note(c, slide, theme):
    note = slide.get("note")
    if not note:
        return
    rounded(c, MARGIN, MARGIN + 0.23 * inch, W - 2 * MARGIN, 0.42 * inch, r=10, fill=hx("#FFF9DB"))
    c.setFillColor(hx("#5F4B00"))
    c.setFont("Helvetica", 8.8)
    c.drawString(MARGIN + 0.16 * inch, MARGIN + 0.39 * inch, clamp(note, 150))


def bullets_slide(c, slide, index, total, theme):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    y = draw_header(c, slide, index, total, theme)
    bullets = slide.get("bullets", [])
    card_h = max(0.62 * inch, min(0.9 * inch, 3.5 * inch / max(len(bullets), 1)))
    for bullet in bullets[:5]:
        rounded(c, MARGIN, y - card_h + 0.08 * inch, W - 2 * MARGIN, card_h, r=16, fill=WHITE, stroke=LINE)
        draw_bullet(c, MARGIN + 0.22 * inch, y - 0.22 * inch, bullet, theme, W - 2 * MARGIN - 0.65 * inch)
        y -= card_h + 0.11 * inch
    draw_note(c, slide, theme)
    c.showPage()


def split_slide(c, slide, index, total, theme):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    y = draw_header(c, slide, index, total, theme)

    left_w = 4.05 * inch
    rounded(c, MARGIN, MARGIN + 0.76 * inch, left_w, y - MARGIN - 0.98 * inch, r=18, fill=WHITE, stroke=LINE)
    ly = y - 0.22 * inch
    for bullet in slide.get("bullets", [])[:4]:
        ly = draw_bullet(c, MARGIN + 0.25 * inch, ly, bullet, theme, left_w - 0.55 * inch)

    rx = MARGIN + left_w + 0.36 * inch
    rw = W - rx - MARGIN
    gradient(c, rx, MARGIN + 0.76 * inch, rw, y - MARGIN - 0.98 * inch, theme["accent"], theme["accent_2"], steps=55)
    rounded(c, rx, MARGIN + 0.76 * inch, rw, y - MARGIN - 0.98 * inch, r=18, fill=colors.Color(1, 1, 1, 0), stroke=None)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 52)
    c.drawString(rx + 0.32 * inch, y - 0.95 * inch, str(index).zfill(2))
    c.setFont("Helvetica-Bold", 17)
    c.drawString(rx + 0.34 * inch, y - 1.35 * inch, clamp(slide.get("callout") or slide.get("heading"), 38))
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.Color(1, 1, 1, 0.82))
    for i, line in enumerate(wrap(c, slide.get("note", ""), "Helvetica", 11, rw - 0.7 * inch)[:5]):
        c.drawString(rx + 0.34 * inch, y - 1.72 * inch - i * 0.18 * inch, line)
    c.showPage()


def grid_slide(c, slide, index, total, theme):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    y = draw_header(c, slide, index, total, theme)
    bullets = slide.get("bullets", [])[:4]
    gap = 0.18 * inch
    card_w = (W - 2 * MARGIN - gap) / 2
    card_h = 1.03 * inch
    for i, bullet in enumerate(bullets):
        col = i % 2
        row = i // 2
        x = MARGIN + col * (card_w + gap)
        cy = y - row * (card_h + gap) - card_h
        rounded(c, x, cy, card_w, card_h, r=18, fill=WHITE, stroke=LINE)
        c.setFillColor(hx(theme["accent"]))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 0.18 * inch, cy + card_h - 0.28 * inch, f"0{i + 1}")
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 15)
        lines = wrap(c, bullet, "Helvetica-Bold", 15, card_w - 0.36 * inch)
        for j, line in enumerate(lines[:3]):
            c.drawString(x + 0.18 * inch, cy + card_h - 0.55 * inch - j * 0.2 * inch, line)
    draw_note(c, slide, theme)
    c.showPage()


def chart_slide(c, slide, index, total, theme):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    y = draw_header(c, slide, index, total, theme)
    bullets = slide.get("bullets", [])[:4]
    chart_x = MARGIN
    chart_y = MARGIN + 0.8 * inch
    chart_w = W - 2 * MARGIN
    chart_h = y - chart_y - 0.18 * inch
    rounded(c, chart_x, chart_y, chart_w, chart_h, r=20, fill=WHITE, stroke=LINE)
    for i, bullet in enumerate(bullets):
        value = 0.36 + (i + 1) * 0.13
        bar_w = (chart_w - 1.8 * inch) * min(value, 0.92)
        by = chart_y + chart_h - 0.65 * inch - i * 0.62 * inch
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 10)
        c.drawString(chart_x + 0.28 * inch, by + 0.08 * inch, clamp(bullet, 34))
        rounded(c, chart_x + 1.75 * inch, by, chart_w - 2.1 * inch, 0.22 * inch, r=6, fill=hx("#ECE7DC"))
        rounded(c, chart_x + 1.75 * inch, by, bar_w, 0.22 * inch, r=6, fill=hx(theme["accent"]))
    c.showPage()


LAYOUTS = [split_slide, grid_slide, bullets_slide, chart_slide]


def normalize_deck(deck):
    slides = deck.get("slides") or []
    for i, slide in enumerate(slides):
        slide.setdefault("heading", f"Slide {i + 1}")
        slide.setdefault("bullets", [])
        slide["bullets"] = [clamp(b, 118) for b in slide.get("bullets", []) if str(b).strip()]
        if not slide["bullets"]:
            slide["bullets"] = ["Clarify the strongest point for this slide."]
    deck["slides"] = slides
    return deck


def render(deck, out_path):
    deck = normalize_deck(deck)
    theme = theme_for(deck)
    c = canvas.Canvas(out_path, pagesize=PAGE)
    c.setTitle(deck.get("title") or "TextShop Deck")
    c.setAuthor("TextShop")
    title_slide(c, deck, theme)
    slides = deck.get("slides", [])
    total = max(1, len(slides))
    for i, slide in enumerate(slides, start=1):
        layout = slide.get("layout")
        fn = {
            "split": split_slide,
            "grid": grid_slide,
            "bullets": bullets_slide,
            "chart": chart_slide,
        }.get(layout)
        if fn is None:
            fn = LAYOUTS[(i - 1) % len(LAYOUTS)]
        fn(c, slide, i, total, theme)
    c.save()
    return out_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--deck-json", required=True)
    p.add_argument("--out", default="deck.pdf")
    args = p.parse_args()

    if args.deck_json == "-":
        deck = json.load(sys.stdin)
    else:
        with open(args.deck_json) as f:
            deck = json.load(f)

    path = render(deck, args.out)
    print(json.dumps({"ok": True, "path": path, "slides": len(deck.get("slides", []))}))


if __name__ == "__main__":
    main()
