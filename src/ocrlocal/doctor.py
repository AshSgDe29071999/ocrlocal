"""Diagnostic checks for the local OCR toolchain."""

from __future__ import annotations

import importlib.metadata
import shutil
import subprocess
from dataclasses import dataclass
from typing import Callable

from ocrlocal import __version__


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def _pkg_version(dist_name: str) -> str | None:
    try:
        return importlib.metadata.version(dist_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def check_tesseract_binary(
    which: Callable[[str], str | None] = shutil.which,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> CheckResult:
    path = which("tesseract")
    if not path:
        return CheckResult(
            name="tesseract binary",
            ok=False,
            detail="not found on PATH — install tesseract-ocr (see README)",
        )
    try:
        proc = run(
            [path, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except OSError as exc:
        return CheckResult(
            name="tesseract binary",
            ok=False,
            detail=f"found at {path} but failed to run: {exc}",
        )
    version_line = (proc.stdout or proc.stderr or "").strip().splitlines()
    version = version_line[0] if version_line else "unknown version"
    return CheckResult(
        name="tesseract binary",
        ok=proc.returncode == 0,
        detail=f"{path} — {version}",
    )


def check_pytesseract() -> CheckResult:
    version = _pkg_version("pytesseract")
    try:
        import pytesseract  # noqa: F401
    except ImportError as exc:
        return CheckResult(
            name="pytesseract",
            ok=False,
            detail=f"import failed: {exc}",
        )
    detail = f"v{version}" if version else "installed"
    return CheckResult(name="pytesseract", ok=True, detail=detail)


def check_pillow() -> CheckResult:
    version = _pkg_version("pillow")
    try:
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        return CheckResult(
            name="Pillow",
            ok=False,
            detail=f"import failed: {exc}",
        )
    detail = f"v{version}" if version else "installed"
    return CheckResult(name="Pillow", ok=True, detail=detail)


def check_ocrlocal() -> CheckResult:
    return CheckResult(
        name="ocrlocal",
        ok=True,
        detail=f"v{__version__}",
    )


def run_doctor(
    which: Callable[[str], str | None] = shutil.which,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[CheckResult]:
    """Run all doctor checks and return results in display order."""
    return [
        check_ocrlocal(),
        check_tesseract_binary(which=which, run=run),
        check_pytesseract(),
        check_pillow(),
    ]


def format_doctor_report(results: list[CheckResult]) -> str:
    """Render an appealing green/red doctor report for the terminal."""
    lines = [
        "ocrlocal doctor",
        "═══════════════",
        "",
    ]
    for result in results:
        mark = "✓" if result.ok else "✗"
        # ANSI colors: green / red / reset
        color = "\033[32m" if result.ok else "\033[31m"
        reset = "\033[0m"
        lines.append(f"  {color}{mark}{reset}  {result.name:<18} {result.detail}")
    lines.append("")
    if all(r.ok for r in results):
        lines.append("\033[32mAll checks passed. Ready for offline OCR.\033[0m")
    else:
        lines.append(
            "\033[31mSome checks failed. Fix the red items, then re-run "
            "`ocrlocal doctor`.\033[0m"
        )
        lines.append(
            "Install Tesseract: apt install tesseract-ocr | brew install tesseract "
            "| choco install tesseract"
        )
    return "\n".join(lines)
