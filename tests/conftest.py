"""Shared fixtures for ocrlocal tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw


@pytest.fixture
def sample_png(tmp_path: Path) -> Path:
    """Create a tiny RGB PNG with drawn text (for integration or open tests)."""
    path = tmp_path / "hello.png"
    img = Image.new("RGB", (200, 60), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 15), "Hello OCR", fill=(0, 0, 0))
    img.save(path)
    return path


@pytest.fixture
def rgba_png(tmp_path: Path) -> Path:
    """PNG in RGBA mode to exercise RGB conversion."""
    path = tmp_path / "rgba.png"
    img = Image.new("RGBA", (40, 20), color=(0, 128, 255, 128))
    img.save(path)
    return path


@pytest.fixture
def not_an_image(tmp_path: Path) -> Path:
    path = tmp_path / "notes.txt"
    path.write_text("this is not an image\n", encoding="utf-8")
    return path
