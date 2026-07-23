# ocrlocal

[![PyPI version](https://img.shields.io/pypi/v/ocrlocal.svg)](https://pypi.org/project/ocrlocal/)
[![Python versions](https://img.shields.io/pypi/pyversions/ocrlocal.svg)](https://pypi.org/project/ocrlocal/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Offline](https://img.shields.io/badge/network-offline-brightgreen.svg)](https://github.com/AshSgDe29071999/ocrlocal)

**Dead-simple offline OCR for developers.** Point it at an image. Get text. No cloud. No API keys.

`ocrlocal` wraps [Tesseract](https://github.com/tesseract-ocr/tesseract) via `pytesseract` + Pillow into a polished CLI with batching, JSON output, and a delightful `doctor` check.

---

## Install

```bash
pip install ocrlocal
```

You also need the **Tesseract** binary on your system:

| Platform | Command |
|----------|---------|
| Debian / Ubuntu | `sudo apt update && sudo apt install -y tesseract-ocr` |
| macOS | `brew install tesseract` |
| Windows (Chocolatey) | `choco install tesseract` |
| Windows (installer) | [UB Mannheim builds](https://github.com/UB-Mannheim/tesseract/wiki) |

Verify everything in one shot:

```bash
ocrlocal doctor
```

---

## 60-second demo

```bash
# Single image → stdout
ocrlocal receipt.png

# Language pass-through (Tesseract style)
ocrlocal scan.png --lang eng+fra

# Batch + JSON for scripts
ocrlocal photos/*.png --json

# Write .txt files into a folder
ocrlocal invoices/*.jpg --out ./text
```

Sample JSON:

```json
[
  {
    "file": "receipt.png",
    "text": "TOTAL 12.50",
    "lang": "eng",
    "engine": "tesseract"
  }
]
```

---

## `ocrlocal doctor`

A green/red health check for your local OCR stack:

```text
ocrlocal doctor
═══════════════

  ✓  ocrlocal           v0.1.0
  ✓  tesseract binary   /usr/bin/tesseract — tesseract 5.3.0
  ✓  pytesseract        v0.3.13
  ✓  Pillow             v10.4.0

All checks passed. Ready for offline OCR.
```

If Tesseract is missing, `doctor` exits with code `2` and points you at apt / brew / choco / the Windows installer.

---

## Features

| Feature | Details |
|---------|---------|
| Offline-only | Never phones home. No network calls. |
| Single or batch | Files and shell globs |
| `--json` | Machine-friendly `{file, text, lang, engine}` list |
| `--lang` | Full Tesseract lang strings (`eng`, `eng+fra`, …) |
| `--out DIR` | Write mirrored `.txt` files |
| Exit codes | `0` ok · `1` OCR/file errors · `2` missing Tesseract/config |
| `-q` / `-V` | Quiet mode · version |
| `doctor` | Binary + library diagnostics |

---

## vs calling pytesseract yourself

| | Raw pytesseract | **ocrlocal** |
|--|-----------------|--------------|
| CLI | DIY | Ready |
| Batch / globs | DIY | Built-in |
| JSON for scripts | DIY | `--json` |
| Missing-binary UX | Cryptic | Install hints + exit `2` |
| Health check | None | `ocrlocal doctor` |
| Output files | DIY | `--out DIR` |

Use the library if you are embedding OCR deep in an app. Use **ocrlocal** when you want a dependable terminal tool.

---

## CLI reference

```text
ocrlocal [OPTIONS] [IMAGES]...
ocrlocal doctor
```

| Option | Meaning |
|--------|---------|
| `--lang / -l` | Tesseract languages (default: `eng`) |
| `--json` | JSON array on stdout |
| `--out DIR` | Write `.txt` files into DIR |
| `-q / --quiet` | Errors only |
| `-V / --version` | Print version |

**Exit codes**

- `0` — success
- `1` — one or more OCR / file errors (partial batch still reports successes)
- `2` — missing Tesseract or broken config

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Tesseract OCR was not found` | Install the system binary (table above), then `ocrlocal doctor` |
| Wrong / empty text | Try a sharper crop; set `--lang` to match the document |
| `Not a supported image file` | Pass a real PNG/JPEG/TIFF/WebP — not a PDF or text file |
| Language data missing | Install packs, e.g. `tesseract-ocr-fra` on Debian |
| Integration tests skipped | Expected without Tesseract; mocked suite still covers behavior |

---

## Development

```bash
git clone https://github.com/AshSgDe29071999/ocrlocal.git
cd ocrlocal
pip install -e ".[dev]"
pytest
```

Integration tests that hit a real Tesseract binary are **skipped automatically** when `tesseract` is not on `PATH`.

---

## License

MIT © AshSgDe29071999
