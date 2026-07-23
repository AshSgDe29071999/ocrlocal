"""Typer CLI for offline OCR."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional, Sequence

import click
import typer
from typer.core import TyperGroup

from ocrlocal import __version__
from ocrlocal.doctor import format_doctor_report, run_doctor
from ocrlocal.errors import (
    EXIT_CONFIG,
    EXIT_OCR_ERROR,
    EXIT_OK,
    DependencyMissingError,
    ImageOpenError,
    OcrProcessError,
    TesseractMissingError,
)
from ocrlocal.ocr import expand_inputs, ocr_image, write_text_output


class DefaultOCRGroup(TyperGroup):
    """Route bare file/glob/option invocations to the hidden `ocr` command."""

    def parse_args(self, ctx: click.Context, args: Sequence[str]) -> list[str]:
        args_list = list(args)
        if args_list:
            first = args_list[0]
            if first not in self.commands and first not in (
                "--help",
                "-h",
                "--version",
                "-V",
            ):
                args_list = ["ocr", *args_list]
        return super().parse_args(ctx, args_list)

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        return super().resolve_command(ctx, args)


app = typer.Typer(
    name="ocrlocal",
    help="Dead-simple offline OCR. No cloud. No API keys.",
    epilog=(
        "Examples:\n"
        "  ocrlocal image.png\n"
        "  ocrlocal photos/*.png --json\n"
        "  ocrlocal scan.png --lang eng+fra --out ./text\n"
        "  ocrlocal doctor"
    ),
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode=None,
    cls=DefaultOCRGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"ocrlocal {__version__}")
        raise typer.Exit(EXIT_OK)


@app.callback()
def _root(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Dead-simple offline OCR. No cloud. No API keys."""


@app.command("ocr", hidden=True)
def ocr_cmd(
    images: list[str] = typer.Argument(
        ...,
        help="Image file(s) or glob patterns to OCR.",
    ),
    lang: str = typer.Option(
        "eng",
        "--lang",
        "-l",
        help="Tesseract language(s), e.g. eng or eng+fra.",
    ),
    json_out: bool = typer.Option(
        False,
        "--json",
        help="Emit a JSON list of {file, text, lang, engine}.",
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        help="Write .txt files into DIR (mirrors basenames).",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Quiet mode: errors only.",
    ),
) -> None:
    """OCR one or more local image files to text."""
    paths = expand_inputs(images)
    if not paths:
        typer.secho("No input files matched.", fg=typer.colors.RED, err=True)
        raise typer.Exit(EXIT_OCR_ERROR)

    results_payload: list[dict[str, str]] = []
    errors = 0

    for path in paths:
        try:
            result = ocr_image(path, lang=lang)
        except TesseractMissingError as exc:
            typer.secho(exc.message, fg=typer.colors.RED, err=True)
            raise typer.Exit(EXIT_CONFIG) from exc
        except DependencyMissingError as exc:
            typer.secho(exc.message, fg=typer.colors.RED, err=True)
            raise typer.Exit(EXIT_CONFIG) from exc
        except (ImageOpenError, OcrProcessError) as exc:
            errors += 1
            typer.secho(exc.message, fg=typer.colors.RED, err=True)
            continue

        results_payload.append(result.to_dict())

        if out is not None:
            write_text_output(result, out)
        elif not json_out and not quiet:
            if len(paths) > 1:
                typer.echo(f"===== {path} =====")
            typer.echo(result.text)

    if json_out:
        typer.echo(json.dumps(results_payload, ensure_ascii=False, indent=2))

    if errors:
        raise typer.Exit(EXIT_OCR_ERROR)
    raise typer.Exit(EXIT_OK)


@app.command("doctor")
def doctor_cmd() -> None:
    """Check Tesseract, pytesseract, and Pillow — green/red report."""
    results = run_doctor()
    typer.echo(format_doctor_report(results))
    if all(r.ok for r in results):
        raise typer.Exit(EXIT_OK)
    raise typer.Exit(EXIT_CONFIG)


def run() -> None:
    """Console-script entry that keeps SystemExit codes clean."""
    try:
        app()
    except SystemExit as exc:
        code = exc.code
        if code is None:
            sys.exit(EXIT_OK)
        if isinstance(code, int):
            sys.exit(code)
        sys.exit(EXIT_OCR_ERROR)


if __name__ == "__main__":
    run()
