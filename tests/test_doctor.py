"""Tests for ocrlocal doctor diagnostics."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from ocrlocal.doctor import (
    check_pillow,
    check_pytesseract,
    check_tesseract_binary,
    format_doctor_report,
    run_doctor,
)


def test_check_tesseract_missing() -> None:
    result = check_tesseract_binary(which=lambda _: None)
    assert result.ok is False
    assert "not found" in result.detail.lower()


def test_check_tesseract_ok() -> None:
    completed = MagicMock(spec=subprocess.CompletedProcess)
    completed.returncode = 0
    completed.stdout = "tesseract 5.3.0\n leptonica\n"
    completed.stderr = ""

    def fake_run(*_a, **_k):
        return completed

    result = check_tesseract_binary(
        which=lambda _: "/usr/bin/tesseract",
        run=fake_run,
    )
    assert result.ok is True
    assert "/usr/bin/tesseract" in result.detail
    assert "5.3.0" in result.detail


def test_check_pytesseract_and_pillow() -> None:
    assert check_pytesseract().ok is True
    assert check_pillow().ok is True


def test_run_doctor_when_tesseract_missing() -> None:
    results = run_doctor(which=lambda _: None)
    by_name = {r.name: r for r in results}
    assert by_name["tesseract binary"].ok is False
    assert by_name["pytesseract"].ok is True
    assert by_name["Pillow"].ok is True
    assert by_name["ocrlocal"].ok is True


def test_format_doctor_report_failure() -> None:
    results = run_doctor(which=lambda _: None)
    report = format_doctor_report(results)
    assert "ocrlocal doctor" in report
    assert "✗" in report
    assert "Some checks failed" in report


def test_format_doctor_report_success() -> None:
    completed = MagicMock(spec=subprocess.CompletedProcess)
    completed.returncode = 0
    completed.stdout = "tesseract 5.0.0\n"
    completed.stderr = ""
    results = run_doctor(
        which=lambda _: "/bin/tesseract",
        run=lambda *_a, **_k: completed,
    )
    report = format_doctor_report(results)
    assert "✓" in report
    assert "All checks passed" in report
