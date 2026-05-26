"""Compose the 7-slide carousel for a given CarouselContent + CTA copy."""
from __future__ import annotations

from pathlib import Path

from ..ai.rewriter import CarouselContent
from .slides import (
    CTASlide,
    ContentSlide,
    CoverSlide,
    LeverageSlide,
    PlaySlide,
    save,
)


def build(content: CarouselContent, cta: dict, out_dir: Path) -> list[Path]:
    """Render 7 PNGs to out_dir, return their paths in order."""
    out_dir.mkdir(parents=True, exist_ok=True)
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
        CTASlide(
            keyword=cta.get("keyword", "STACK"),
            offer_body=cta.get("offer_body", ""),
        ),
    ]
    paths: list[Path] = []
    for i, s in enumerate(slides, start=1):
        p = out_dir / f"slide_{i}.png"
        save(s.render(), p)
        paths.append(p)
    return paths
