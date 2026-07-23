"""Unit tests for OCR core helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from ocrlocal.errors import ImageOpenError, OcrProcessError, TesseractMissingError
from ocrlocal.ocr import (
    OcrResult,
    expand_inputs,
    ocr_image,
    open_image,
    require_tesseract,
    write_text_output,
)


def test_require_tesseract_missing() -> None:
    with patch("ocrlocal.ocr.shutil.which", return_value=None):
        with pytest.raises(TesseractMissingError) as exc:
            require_tesseract()
    msg = str(exc.value).lower()
    assert "apt" in msg
    assert "brew" in msg
    assert "choco" in msg
    assert "ub-mannheim" in msg


def test_require_tesseract_found() -> None:
    with patch("ocrlocal.ocr.shutil.which", return_value="/usr/bin/tesseract"):
        assert require_tesseract() == "/usr/bin/tesseract"


def test_open_image_rgb(sample_png: Path) -> None:
    img = open_image(sample_png)
    assert img.mode in ("RGB", "L")
    img.close()


def test_open_image_converts_rgba(rgba_png: Path) -> None:
    img = open_image(rgba_png)
    assert img.mode == "RGB"
    img.close()


def test_open_image_rejects_non_image(not_an_image: Path) -> None:
    with pytest.raises(ImageOpenError) as exc:
        open_image(not_an_image)
    assert "Not a supported image" in str(exc.value)


def test_open_image_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ImageOpenError):
        open_image(tmp_path / "missing.png")


def test_ocr_image_mocked(sample_png: Path) -> None:
    with patch("ocrlocal.ocr.require_tesseract", return_value="/usr/bin/tesseract"):
        with patch("pytesseract.image_to_string", return_value="Hello OCR\n") as mocked:
            result = ocr_image(sample_png, lang="eng+fra")
            mocked.assert_called_once()
            assert result.text == "Hello OCR"
            assert result.lang == "eng+fra"
            assert result.engine == "tesseract"
            assert result.file == str(sample_png)
            assert set(result.to_dict()) == {"file", "text", "lang", "engine"}


def test_ocr_image_tesseract_missing_via_pytesseract(sample_png: Path) -> None:
    import pytesseract

    with patch("ocrlocal.ocr.require_tesseract", return_value="/usr/bin/tesseract"):
        with patch(
            "pytesseract.image_to_string",
            side_effect=pytesseract.TesseractNotFoundError(),
        ):
            with pytest.raises(TesseractMissingError):
                ocr_image(sample_png)


def test_ocr_image_process_error(sample_png: Path) -> None:
    import pytesseract

    with patch("ocrlocal.ocr.require_tesseract", return_value="/usr/bin/tesseract"):
        with patch(
            "pytesseract.image_to_string",
            side_effect=pytesseract.TesseractError("status", "boom"),
        ):
            with pytest.raises(OcrProcessError) as exc:
                ocr_image(sample_png)
    assert "OCR failed" in str(exc.value)


def test_expand_inputs_literal_and_dedupe(sample_png: Path) -> None:
    paths = expand_inputs([str(sample_png), str(sample_png)])
    assert len(paths) == 1


def test_expand_inputs_glob(tmp_path: Path) -> None:
    (tmp_path / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (tmp_path / "b.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    matches = expand_inputs([str(tmp_path / "*.png")])
    assert {p.name for p in matches} == {"a.png", "b.png"}


def test_write_text_output_to_dir(tmp_path: Path, sample_png: Path) -> None:
    out_dir = tmp_path / "out"
    result = OcrResult(file=str(sample_png), text="hi", lang="eng")
    out_path = write_text_output(result, out_dir)
    assert out_path == out_dir / "hello.txt"
    assert out_path.read_text(encoding="utf-8") == "hi\n"
