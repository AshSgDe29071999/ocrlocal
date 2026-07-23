"""Typed errors and exit-code helpers for ocrlocal."""

from __future__ import annotations

from typing import Final

EXIT_OK: Final[int] = 0
EXIT_OCR_ERROR: Final[int] = 1
EXIT_CONFIG: Final[int] = 2


class OcrLocalError(Exception):
    """Base error for ocrlocal."""

    exit_code: int = EXIT_OCR_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TesseractMissingError(OcrLocalError):
    """Raised when the Tesseract binary cannot be found."""

    exit_code = EXIT_CONFIG


class DependencyMissingError(OcrLocalError):
    """Raised when a required Python dependency is missing or broken."""

    exit_code = EXIT_CONFIG


class ImageOpenError(OcrLocalError):
    """Raised when an image cannot be opened or is not a supported image."""

    exit_code = EXIT_OCR_ERROR


class OcrProcessError(OcrLocalError):
    """Raised when OCR fails for a specific file."""

    exit_code = EXIT_OCR_ERROR


TESSERACT_INSTALL_HINT = """\
Tesseract OCR was not found on this system.

ocrlocal needs the Tesseract binary installed and available on PATH.

Install hints:

  Debian / Ubuntu:
    sudo apt update && sudo apt install -y tesseract-ocr

  macOS (Homebrew):
    brew install tesseract

  Windows (Chocolatey):
    choco install tesseract

  Windows (installer):
    https://github.com/UB-Mannheim/tesseract/wiki

After installing, confirm with:
  tesseract --version
  ocrlocal doctor
"""
