# PrintWatch Desktop

A local-first desktop app for viewing and cycling through multiple 3D-printer camera streams.
It began as an ELEGOO webcam utility and is being developed into a public, cross-platform
product for Windows, macOS, and Linux.

> [!IMPORTANT]
> PrintWatch Desktop is an independent open-source project. It is not affiliated with,
> endorsed by, or supported by ELEGOO. ELEGOO and Matrix are trademarks of their respective
> owners.

## Product status

**Alpha / pre-release.** The core multi-camera experience is implemented, but code signing,
installer validation, hardware compatibility testing, accessibility review, and release
artifacts must pass the gates in [`docs/RELEASE_PLAN.md`](docs/RELEASE_PLAN.md) before a
stable public release.

## What works today

- Add, edit, and remove multiple printer camera profiles.
- View HTTP, HTTPS, and MJPEG-style browser streams.
- Automatically cycle between two or more cameras at a configurable interval.
- Capture screenshots to PNG or JPEG.
- Keep the window above other applications.
- Save camera configuration locally with atomic writes and corrupt-file recovery.
- Run from the same Python source on Windows, macOS, and Linux.
- Build native artifacts through GitHub Actions.

## Supported connections

The initial release intentionally focuses on local camera viewing:

- ELEGOO-style MJPEG stream: `http://<printer-ip>:3031/video`
- Generic HTTP/MJPEG camera or printer stream

Credentials embedded in URLs are rejected because the configuration is stored locally as
plain JSON. Authenticated cameras need a future secure credential-store adapter.

## Install from source

Python 3.11 or 3.12 is recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
printwatch
```

### CachyOS / Arch Linux

```bash
sudo pacman -S --needed python python-pip qt6-webengine
python -m venv .venv
source .venv/bin/activate
pip install -e .
printwatch
```

A signed Windows installer, Apple Silicon `.app`, and Linux release package are produced by
the release workflow. The Linux package is expected to work on current CachyOS systems, but
CachyOS remains a required release-test target.

## Development

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
python -m compileall src
```

## Building locally

```bash
pip install -e ".[dev]"
pyinstaller --clean --noconfirm packaging/printwatch.spec
```

PyInstaller must run on each target operating system; it does not cross-compile native
packages.

## Design and release documents

- [`docs/SDD.md`](docs/SDD.md) — product specification and implementation plan
- [`docs/RELEASE_PLAN.md`](docs/RELEASE_PLAN.md) — public-release gates and milestones
- [`docs/MATRIX_INTEGRATION.md`](docs/MATRIX_INTEGRATION.md) — safe integration strategy
- [`SECURITY.md`](SECURITY.md) — vulnerability reporting and local-data model

## Why this exists

Phone apps are useful away from a desk, but makers often want a small desktop window beside
their slicer, terminal, or browser. PrintWatch was created to monitor an FDM printer and a
resin printer without repeatedly reaching for a phone or opening separate browser tabs.
