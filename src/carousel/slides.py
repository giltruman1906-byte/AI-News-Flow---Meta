"""Slide renderers for the 7-slide Suki AI News carousel. PIL-based.

Slide types match the mockup in example_carusel_mocup/:
  1  CoverSlide        — dark bg, hook headline + subtitle
  2  PlaySlide          — cream bg, big statement with accent phrase
  3-5 ContentSlide      — cream bg, numbered "01"–"03", headline + body
  6  LeverageSlide      — dark bg, big orange stat comparison
  7  CTASlide           — dark bg, "Comment KEYWORD" CTA
"""
from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .theme import COLORS, FONTS, SPACING

log = logging.getLogger(__name__)

TOTAL_SLIDES = 7


def _font(path: str, size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype(path, size=size)
    except Exception:
        return ImageFont.load_default()


def _canvas(bg: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (SPACING.slide_w, SPACING.slide_h), bg)
    return img, ImageDraw.Draw(img)


def _draw_suki_logo(draw: ImageDraw.ImageDraw, x: int, y: int, color: str = COLORS.text_light) -> None:
    """Draw a simplified Suki wave logo (three strokes)."""
    for i in range(3):
        y0 = y + i * 12
        draw.line((x, y0 + 6, x + 35, y0), fill=color, width=3)


def _footer(draw: ImageDraw.ImageDraw, index: int, dark_bg: bool) -> None:
    f = _font(FONTS.mono, 20)
    text_col = COLORS.text_muted_light if dark_bg else COLORS.text_muted_dark
    y = SPACING.slide_h - SPACING.padding
    draw.text((SPACING.padding, y), "WWW.SUKI-SYSTEMS.COM", fill=text_col, font=f)
    indicator = f"{index:02d} / {TOTAL_SLIDES:02d}"
    bbox = draw.textbbox((0, 0), indicator, font=f)
    w = bbox[2] - bbox[0]
    draw.text((SPACING.slide_w - SPACING.padding - w, y), indicator, fill=text_col, font=f)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for w in words:
        trial = " ".join(cur + [w])
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width or not cur:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


class CoverSlide:
    """Slide 1: dark navy, hook headline + subtitle."""

    def __init__(self, hook: str, subtitle: str, date_label: str = "AI NEWS"):
        self.hook = hook
        self.subtitle = subtitle
        self.date_label = date_label

    def render(self) -> Image.Image:
        img, draw = _canvas(COLORS.bg_dark)
        pad = SPACING.padding

        _draw_suki_logo(draw, pad, pad)
        header_font = _font(FONTS.mono, 20)
        draw.ellipse((pad + 55, pad + 8, pad + 67, pad + 20), fill=COLORS.accent)
        draw.text((pad + 78, pad + 4), self.date_label, fill=COLORS.text_muted_light, font=header_font)

        head_font = _font(FONTS.display, 120)
        max_w = SPACING.slide_w - 2 * pad
        lines = _wrap(draw, self.hook.upper(), head_font, max_w)
        line_h = 135
        y = SPACING.slide_h // 2 - (line_h * len(lines)) // 2 - 40
        for ln in lines:
            draw.text((pad, y), ln, fill=COLORS.text_light, font=head_font)
            y += line_h

        y += 20
        body_font = _font(FONTS.body, 36)
        for ln in _wrap(draw, self.subtitle, body_font, max_w):
            draw.text((pad, y), ln, fill=COLORS.text_muted_light, font=body_font)
            y += 48

        _footer(draw, 1, dark_bg=True)
        return img


class PlaySlide:
    """Slide 2: cream bg, big bold statement. Accent phrase rendered in orange."""

    def __init__(self, statement: str, accent_phrase: str = ""):
        self.statement = statement
        self.accent_phrase = accent_phrase

    def render(self) -> Image.Image:
        img, draw = _canvas(COLORS.bg_cream)
        pad = SPACING.padding

        _draw_suki_logo(draw, pad, pad, COLORS.text_dark)
        label_font = _font(FONTS.mono, 20)
        draw.text((pad + 55, pad + 4), "THE PLAY", fill=COLORS.text_dark, font=label_font)

        head_font = _font(FONTS.display_heavy, 80)
        max_w = SPACING.slide_w - 2 * pad
        lines = _wrap(draw, self.statement, head_font, max_w)
        line_h = 95
        y = SPACING.slide_h // 2 - (line_h * len(lines)) // 2

        accent_lower = self.accent_phrase.lower()
        for ln in lines:
            if accent_lower and accent_lower in ln.lower():
                idx = ln.lower().index(accent_lower)
                before = ln[:idx]
                accent_part = ln[idx:idx + len(self.accent_phrase)]
                after = ln[idx + len(self.accent_phrase):]
                x = pad
                if before:
                    draw.text((x, y), before, fill=COLORS.text_dark, font=head_font)
                    x += draw.textbbox((0, 0), before, font=head_font)[2]
                draw.text((x, y), accent_part, fill=COLORS.accent, font=head_font)
                x += draw.textbbox((0, 0), accent_part, font=head_font)[2]
                if after:
                    draw.text((x, y), after, fill=COLORS.text_dark, font=head_font)
            else:
                draw.text((pad, y), ln, fill=COLORS.text_dark, font=head_font)
            y += line_h

        _footer(draw, 2, dark_bg=False)
        return img


class ContentSlide:
    """Slides 3-5: cream bg, numbered content card."""

    def __init__(self, number: int, headline: str, body: str, index: int):
        self.number = number
        self.headline = headline
        self.body = body
        self.index = index

    def render(self) -> Image.Image:
        img, draw = _canvas(COLORS.bg_cream)
        pad = SPACING.padding

        _draw_suki_logo(draw, pad, pad, COLORS.text_dark)

        num_font = _font(FONTS.display, 64)
        y = pad + 120
        num_str = f"{self.number:02d}"
        draw.text((pad, y), num_str[0], fill=COLORS.accent, font=num_font)
        x0 = pad + draw.textbbox((0, 0), num_str[0], font=num_font)[2] + 2
        draw.text((x0, y), num_str[1], fill=COLORS.text_dark, font=num_font)
        y += 80

        divider_w = SPACING.slide_w - 2 * pad
        draw.line((pad, y, pad + divider_w, y), fill=COLORS.text_muted_dark, width=2)
        y += 40

        head_font = _font(FONTS.display_heavy, 80)
        max_w = SPACING.slide_w - 2 * pad
        for ln in _wrap(draw, self.headline, head_font, max_w):
            draw.text((pad, y), ln, fill=COLORS.text_dark, font=head_font)
            y += 95

        y += 20
        body_font = _font(FONTS.body, 34)
        for ln in _wrap(draw, self.body, body_font, max_w):
            draw.text((pad, y), ln, fill=COLORS.text_dark, font=body_font)
            y += 46

        _footer(draw, self.index, dark_bg=False)
        return img


class LeverageSlide:
    """Slide 6: dark bg, big orange stat comparison."""

    def __init__(self, stat_top: str, stat_bottom: str, body: str):
        self.stat_top = stat_top
        self.stat_bottom = stat_bottom
        self.body = body

    def render(self) -> Image.Image:
        img, draw = _canvas(COLORS.bg_dark)
        pad = SPACING.padding

        _draw_suki_logo(draw, pad, pad)
        label_font = _font(FONTS.mono, 20)
        draw.text((pad + 55, pad + 4), "THE LEVERAGE", fill=COLORS.text_muted_light, font=label_font)

        big_font = _font(FONTS.display, 160)
        vs_font = _font(FONTS.display, 80)
        max_w = SPACING.slide_w - 2 * pad

        y = pad + 120
        for ln in _wrap(draw, self.stat_top, big_font, max_w):
            draw.text((pad, y), ln, fill=COLORS.text_light, font=big_font)
            y += 170

        draw.text((pad, y), "vs", fill=COLORS.accent, font=vs_font)
        y += 100

        for ln in _wrap(draw, self.stat_bottom, big_font, max_w):
            draw.text((pad, y), ln, fill=COLORS.accent, font=big_font)
            y += 170

        y += 20
        body_font = _font(FONTS.body, 34)
        for ln in _wrap(draw, self.body, body_font, max_w):
            draw.text((pad, y), ln, fill=COLORS.text_muted_light, font=body_font)
            y += 46

        _footer(draw, 6, dark_bg=True)
        return img


class CTASlide:
    """Slide 7: dark bg, keyword CTA (Instagram version)."""

    def __init__(self, keyword: str, offer_body: str):
        self.keyword = keyword
        self.offer_body = offer_body

    def render(self) -> Image.Image:
        img, draw = _canvas(COLORS.bg_dark)
        pad = SPACING.padding

        label_font = _font(FONTS.mono, 20)
        draw.text((pad, pad + 4), "YOUR MOVE", fill=COLORS.text_muted_light, font=label_font)

        comment_font = _font(FONTS.display_heavy, 100)
        keyword_font = _font(FONTS.display, 140)
        y = SPACING.slide_h // 2 - 200
        draw.text((pad, y), "Comment", fill=COLORS.text_light, font=comment_font)
        y += 130
        draw.text((pad, y), self.keyword.upper(), fill=COLORS.accent, font=keyword_font)
        y += 140

        body_font = _font(FONTS.body, 34)
        max_w = SPACING.slide_w - 2 * pad
        for ln in _wrap(draw, self.offer_body, body_font, max_w):
            draw.text((SPACING.slide_w // 2 - draw.textbbox((0, 0), ln, font=body_font)[2] // 2, y),
                      ln, fill=COLORS.text_muted_light, font=body_font)
            y += 46

        logo_y = SPACING.slide_h - pad - 60
        _draw_suki_logo(draw, SPACING.slide_w // 2 - 80, logo_y)
        brand_font = _font(FONTS.display, 24)
        draw.text((SPACING.slide_w // 2 - 80 + 50, logo_y + 6), "SUKI SYSTEMS",
                  fill=COLORS.text_light, font=brand_font)

        _footer(draw, 7, dark_bg=True)
        return img


class FBCTASlide:
    """Slide 7: dark bg, 'Read full article' CTA (Facebook version)."""

    def __init__(self, offer_body: str = ""):
        self.offer_body = offer_body

    def render(self) -> Image.Image:
        img, draw = _canvas(COLORS.bg_dark)
        pad = SPACING.padding

        label_font = _font(FONTS.mono, 20)
        draw.text((pad, pad + 4), "YOUR MOVE", fill=COLORS.text_muted_light, font=label_font)

        head_font = _font(FONTS.display_heavy, 100)
        arrow_font = _font(FONTS.display, 120)
        y = SPACING.slide_h // 2 - 200
        for ln in _wrap(draw, "Read the full article", head_font, SPACING.slide_w - 2 * pad):
            draw.text((pad, y), ln, fill=COLORS.text_light, font=head_font)
            y += 120
        y += 20
        draw.text((pad, y), "↓", fill=COLORS.accent, font=arrow_font)
        link_font = _font(FONTS.body, 40)
        draw.text((pad + 100, y + 30), "Link below", fill=COLORS.accent, font=link_font)
        y += 160

        if self.offer_body:
            body_font = _font(FONTS.body, 34)
            max_w = SPACING.slide_w - 2 * pad
            for ln in _wrap(draw, self.offer_body, body_font, max_w):
                draw.text((SPACING.slide_w // 2 - draw.textbbox((0, 0), ln, font=body_font)[2] // 2, y),
                          ln, fill=COLORS.text_muted_light, font=body_font)
                y += 46

        logo_y = SPACING.slide_h - pad - 60
        _draw_suki_logo(draw, SPACING.slide_w // 2 - 80, logo_y)
        brand_font = _font(FONTS.display, 24)
        draw.text((SPACING.slide_w // 2 - 80 + 50, logo_y + 6), "SUKI SYSTEMS",
                  fill=COLORS.text_light, font=brand_font)

        _footer(draw, 7, dark_bg=True)
        return img


def save(img: Image.Image, path: Path) -> None:
    img.save(path, format="PNG", optimize=True)
