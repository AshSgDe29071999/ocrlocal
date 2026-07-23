"""CLI tests via Typer CliRunner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ocrlocal import __version__
from ocrlocal.cli import app
from ocrlocal.doctor import CheckResult
from ocrlocal.ocr import OcrResult

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["-V"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "offline" in result.stdout.lower() or "ocr" in result.stdout.lower()
    assert "doctor" in result.stdout.lower()


def test_doctor_missing_tesseract() -> None:
    with patch("ocrlocal.cli.run_doctor") as mocked:
        mocked.return_value = [
            CheckResult("ocrlocal", True, "v0.1.0"),
            CheckResult("tesseract binary", False, "not found on PATH"),
            CheckResult("pytesseract", True, "v0.3.10"),
            CheckResult("Pillow", True, "v10.0.0"),
        ]
        with patch("ocrlocal.cli.format_doctor_report", return_value="FAIL REPORT\n"):
            result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 2
    assert "FAIL REPORT" in result.stdout


def test_doctor_all_ok() -> None:
    with patch("ocrlocal.cli.run_doctor") as mocked:
        mocked.return_value = [
            CheckResult("ocrlocal", True, "v0.1.0"),
            CheckResult("tesseract binary", True, "/usr/bin/tesseract — tesseract 5"),
            CheckResult("pytesseract", True, "v0.3.10"),
            CheckResult("Pillow", True, "v10.0.0"),
        ]
        with patch("ocrlocal.cli.format_doctor_report", return_value="OK REPORT\n"):
            result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "OK REPORT" in result.stdout


def test_json_output_shape(sample_png: Path) -> None:
    fake = OcrResult(file=str(sample_png), text="hi", lang="eng")
    with patch("ocrlocal.cli.ocr_image", return_value=fake):
        result = runner.invoke(app, [str(sample_png), "--json"])
    assert result.exit_code == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
    assert payload[0]["file"] == str(sample_png)
    assert payload[0]["text"] == "hi"
    assert payload[0]["lang"] == "eng"
    assert payload[0]["engine"] == "tesseract"


def test_batch_partial_failure(sample_png: Path, not_an_image: Path) -> None:
    def fake_ocr(path: Path, lang: str = "eng") -> OcrResult:
        if path.suffix == ".txt":
            from ocrlocal.errors import ImageOpenError

            raise ImageOpenError(f"Not a supported image file: {path}")
        return OcrResult(file=str(path), text="ok", lang=lang)

    with patch("ocrlocal.cli.ocr_image", side_effect=fake_ocr):
        result = runner.invoke(app, [str(sample_png), str(not_an_image), "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert len(payload) == 1
    assert payload[0]["text"] == "ok"


def test_out_dir_writes_txt(tmp_path: Path, sample_png: Path) -> None:
    out_dir = tmp_path / "texts"
    fake = OcrResult(file=str(sample_png), text="saved", lang="eng")
    with patch("ocrlocal.cli.ocr_image", return_value=fake):
        result = runner.invoke(app, [str(sample_png), "--out", str(out_dir), "-q"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert (out_dir / "hello.txt").read_text(encoding="utf-8") == "saved\n"


def test_missing_tesseract_exit_code_2(sample_png: Path) -> None:
    from ocrlocal.errors import TesseractMissingError

    with patch(
        "ocrlocal.cli.ocr_image",
        side_effect=TesseractMissingError("missing tesseract"),
    ):
        result = runner.invoke(app, [str(sample_png)])
    assert result.exit_code == 2
    combined = (result.stderr + result.stdout).lower()
    assert "missing tesseract" in combined


def test_no_match_exit_1(tmp_path: Path) -> None:
    result = runner.invoke(app, [str(tmp_path / "nope-*.png")])
    assert result.exit_code == 1


def test_lang_passthrough(sample_png: Path) -> None:
    seen: dict[str, str] = {}

    def fake_ocr(path: Path, lang: str = "eng") -> OcrResult:
        seen["lang"] = lang
        return OcrResult(file=str(path), text="x", lang=lang)

    with patch("ocrlocal.cli.ocr_image", side_effect=fake_ocr):
        result = runner.invoke(app, [str(sample_png), "--lang", "eng+fra", "--json"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert seen["lang"] == "eng+fra"


def test_options_before_files(sample_png: Path) -> None:
    fake = OcrResult(file=str(sample_png), text="hi", lang="deu")
    with patch("ocrlocal.cli.ocr_image", return_value=fake) as mocked:
        result = runner.invoke(app, ["--lang", "deu", str(sample_png), "--json"])
    assert result.exit_code == 0, result.stdout + result.stderr
    mocked.assert_called_once()
    assert mocked.call_args.kwargs.get("lang") == "deu" or mocked.call_args[1].get("lang") == "deu" or (
        len(mocked.call_args[0]) > 1 and mocked.call_args[0][1] == "deu"
    ) or mocked.call_args == ((sample_png,), {"lang": "deu"}) or True
    # lang is keyword-only in signature as lang=
    assert mocked.call_args.kwargs["lang"] == "deu"
