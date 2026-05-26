"""Brand tokens — matched to Suki Systems carousel mockup."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent.parent / "assets"
FONTS_DIR = ASSETS / "fonts"


@dataclass(frozen=True)
class Colors:
    bg_dark: str = "#1B2033"
    bg_cream: str = "#F5F0EB"
    text_light: str = "#FFFFFF"
    text_dark: str = "#1B2033"
    text_muted_light: str = "#8A8FA0"
    text_muted_dark: str = "#7A7568"
    accent: str = "#E85D26"


@dataclass(frozen=True)
class Fonts:
    display: str = str(FONTS_DIR / "BebasNeue-Regular.ttf")
    display_heavy: str = str(FONTS_DIR / "Inter-ExtraBold.ttf")
    body: str = str(FONTS_DIR / "Inter-Regular.ttf")
    mono: str = str(FONTS_DIR / "JetBrainsMono-Regular.ttf")


@dataclass(frozen=True)
class Spacing:
    slide_w: int = 1080
    slide_h: int = 1350
    padding: int = 80
    section_gap: int = 48


COLORS = Colors()
FONTS = Fonts()
SPACING = Spacing()
