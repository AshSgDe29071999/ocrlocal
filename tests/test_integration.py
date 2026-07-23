"""Optional real Tesseract integration test.

Skipped automatically when the `tesseract` binary is not on PATH.
CI without Tesseract still runs the full mocked suite.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ocrlocal.cli import app
from ocrlocal.ocr import ocr_image

pytestmark = pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="tesseract binary not installed — integration test skipped",
)

runner = CliRunner()


def test_real_ocr_roundtrip(sample_png: Path) -> None:
    result = ocr_image(sample_png, lang="eng")
    assert result.engine == "tesseract"
    assert isinstance(result.text, str)


def test_real_cli_stdout(sample_png: Path) -> None:
    result = runner.invoke(app, [str(sample_png)])
    assert result.exit_code == 0
