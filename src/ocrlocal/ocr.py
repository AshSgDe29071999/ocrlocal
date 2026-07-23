"""Core offline OCR helpers (no network calls)."""

from __future__ import annotations

import glob
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence

from ocrlocal.errors import (
    ImageOpenError,
    OcrProcessError,
    TESSERACT_INSTALL_HINT,
    TesseractMissingError,
)

ENGINE_NAME = "tesseract"


@dataclass(frozen=True)
class OcrResult:
    """OCR output for a single image file."""

    file: str
    text: str
    lang: str
    engine: str = ENGINE_NAME

    def to_dict(self) -> dict[str, str]:
        return {
            "file": self.file,
            "text": self.text,
            "lang": self.lang,
            "engine": self.engine,
        }


def require_tesseract() -> str:
    """Return the Tesseract binary path or raise with install hints."""
    path = shutil.which("tesseract")
    if not path:
        raise TesseractMissingError(TESSERACT_INSTALL_HINT)
    return path


def expand_inputs(patterns: Sequence[str]) -> list[Path]:
    """Expand file paths and globs into a deterministic unique list."""
    found: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        if any(ch in pattern for ch in "*?[]"):
            matches = [Path(p) for p in sorted(glob.glob(pattern))]
        else:
            matches = [Path(pattern)]

        for match in matches:
            key = match.resolve() if match.exists() else match.absolute()
            if key in seen:
                continue
            seen.add(key)
            found.append(match)
    return found


def open_image(path: Path):
    """Open an image with Pillow, converting to RGB when needed."""
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError as exc:  # pragma: no cover
        from ocrlocal.errors import DependencyMissingError

        raise DependencyMissingError(
            "Pillow is not installed. Install with: pip install pillow"
        ) from exc

    try:
        img = Image.open(path)
        img.load()
    except FileNotFoundError as exc:
        raise ImageOpenError(f"File not found: {path}") from exc
    except UnidentifiedImageError as exc:
        raise ImageOpenError(f"Not a supported image file: {path}") from exc
    except OSError as exc:
        raise ImageOpenError(f"Cannot open image '{path}': {exc}") from exc

    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    return img


def ocr_image(path: Path, lang: str = "eng") -> OcrResult:
    """Run Tesseract OCR on a single image path."""
    require_tesseract()
    try:
        import pytesseract
    except ImportError as exc:  # pragma: no cover
        from ocrlocal.errors import DependencyMissingError

        raise DependencyMissingError(
            "pytesseract is not installed. Install with: pip install pytesseract"
        ) from exc

    img = open_image(path)
    try:
        text = pytesseract.image_to_string(img, lang=lang)
    except pytesseract.TesseractNotFoundError as exc:
        raise TesseractMissingError(TESSERACT_INSTALL_HINT) from exc
    except pytesseract.TesseractError as exc:
        raise OcrProcessError(f"OCR failed for '{path}': {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        raise OcrProcessError(f"OCR failed for '{path}': {exc}") from exc
    finally:
        img.close()

    return OcrResult(file=str(path), text=text.rstrip("\n"), lang=lang)


def ocr_paths(
    paths: Sequence[Path], lang: str = "eng"
) -> Iterator[tuple[Path, OcrResult | OcrProcessError | ImageOpenError]]:
    """OCR many paths, yielding either a result or a per-file error."""
    for path in paths:
        try:
            yield path, ocr_image(path, lang=lang)
        except (ImageOpenError, OcrProcessError) as exc:
            yield path, exc


def write_text_output(result: OcrResult, out_dir: Path | None) -> Path:
    """Write OCR text to a .txt file, mirroring the source basename."""
    src = Path(result.file)
    target_dir = out_dir if out_dir is not None else src.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / f"{src.stem}.txt"
    out_path.write_text(result.text + ("\n" if result.text else ""), encoding="utf-8")
    return out_path
