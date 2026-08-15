import argparse
import json
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

PAGE = landscape((10 * inch, 5.625 * inch))
W, H = PAGE
MARGIN = 0.7 * inch
INK = colors.HexColor("#111318")
MUTED = colors.HexColor("#6B7280")
ACCENT = colors.HexColor("#2563EB")


def wrap(c, text, font, size, max_width):
    c.setFont(font, size)
    words = text.split()
    lines = []
    line = ""
    for w in words:
        trial = f"{line} {w}".strip()
        if c.stringWidth(trial, font, size) <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def title_slide(c, deck):
    c.setFillColor(INK)
    for i, line in enumerate(wrap(c, deck.get("title", ""), "Helvetica-Bold", 40, W - 2 * MARGIN)):
        c.setFont("Helvetica-Bold", 40)
        c.drawString(MARGIN, H - MARGIN - 40 - i * 46, line)
    c.setFillColor(MUTED)
    for i, line in enumerate(wrap(c, deck.get("subtitle", ""), "Helvetica", 16, W - 2 * MARGIN)):
        c.setFont("Helvetica", 16)
        c.drawString(MARGIN, H - MARGIN - 140 - i * 22, line)
    c.setStrokeColor(ACCENT)
    c.setLineWidth(3)
    c.line(MARGIN, MARGIN + 20, MARGIN + 1.4 * inch, MARGIN + 20)
    c.showPage()


def content_slide(c, slide, index, total):
    c.setFillColor(INK)
    y = H - MARGIN - 26
    for line in wrap(c, slide.get("heading", ""), "Helvetica-Bold", 26, W - 2 * MARGIN):
        c.setFont("Helvetica-Bold", 26)
        c.drawString(MARGIN, y, line)
        y -= 32

    y -= 12
    c.setFillColor(INK)
    for bullet in slide.get("bullets", []):
        lines = wrap(c, bullet, "Helvetica", 15, W - 2 * MARGIN - 24)
        c.setFillColor(ACCENT)
        c.circle(MARGIN + 5, y + 5, 3, fill=1, stroke=0)
        c.setFillColor(INK)
        for j, line in enumerate(lines):
            c.setFont("Helvetica", 15)
            c.drawString(MARGIN + 20, y - j * 20, line)
        y -= len(lines) * 20 + 12
        if y < MARGIN + 40:
            break

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawRightString(W - MARGIN, MARGIN, f"{index} / {total}")
    c.showPage()


def render(deck, out_path):
    c = canvas.Canvas(out_path, pagesize=PAGE)
    title_slide(c, deck)
    slides = deck.get("slides", [])
    for i, slide in enumerate(slides, start=1):
        content_slide(c, slide, i, len(slides))
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
