"""Compose the 7-slide carousel for a given CarouselContent + CTA copy."""
from __future__ import annotations

from pathlib import Path

from ..ai.rewriter import CarouselContent
from .slides import (
    ContentSlide,
    CoverSlide,
    FBCTASlide,
    IGBookingCTASlide,
    LeverageSlide,
    PlaySlide,
    save,
)


def build(content: CarouselContent, cta: dict, out_dir: Path, platform: str = "ig") -> list[Path]:
    """Render 7 PNGs to out_dir, return their paths in order.

    platform: "ig" for Instagram (Comment CTA), "fb" for Facebook (Read article CTA).
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    if platform == "fb":
        cta_slide = FBCTASlide(offer_body=cta.get("offer_body", ""))
    else:
        cta_slide = IGBookingCTASlide(booking_url=cta.get("booking_url", "cal.com/suki-systems/30min"))

    slides = [
        CoverSlide(
            hook=content.slide_1_hook,
            subtitle=content.slide_1_subtitle,
            date_label=content.date_label,
        ),
        PlaySlide(
            statement=content.slide_2_play,
            accent_phrase=content.slide_2_accent,
        ),
        ContentSlide(number=1, headline=content.slide_3_headline, body=content.slide_3_body, index=3),
        ContentSlide(number=2, headline=content.slide_4_headline, body=content.slide_4_body, index=4),
        ContentSlide(number=3, headline=content.slide_5_headline, body=content.slide_5_body, index=5),
        LeverageSlide(
            stat_top=content.slide_6_stat_top,
            stat_bottom=content.slide_6_stat_bottom,
            body=content.slide_6_body,
        ),
        cta_slide,
    ]
    paths: list[Path] = []
    for i, s in enumerate(slides, start=1):
        p = out_dir / f"slide_{i}.png"
        save(s.render(), p)
        paths.append(p)
    return paths
