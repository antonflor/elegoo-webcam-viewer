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
installer validation, hardware compatibility testing, accessibility review, and the remaining
gates in [`docs/RELEASE_PLAN.md`](docs/RELEASE_PLAN.md) must pass before a stable public
release.

## What works today

- Add, edit, and remove multiple printer camera profiles.
- View direct HTTP or HTTPS MJPEG/JPEG streams without an embedded browser.
- Automatically reconnect with bounded exponential backoff.
- Automatically cycle between two or more cameras at a configurable interval.
- Capture the original camera frame to PNG or JPEG.
- Keep the window above other applications.
- Save camera configuration locally with atomic writes and corrupt-file recovery.
- Run from the same Python source on Windows, macOS, and Linux.
- Build native artifacts through GitHub Actions.

## Supported connections

The initial release intentionally focuses on direct local camera streams:

- ELEGOO-style MJPEG stream: `http://<printer-ip>:3031/video`
- Generic direct MJPEG stream
- Direct JPEG snapshot endpoint, refreshed automatically

HTML camera dashboards, HLS, WebRTC, and RTSP are not supported in the initial release. This
narrower protocol contract removes the Chromium/WebEngine runtime, reduces package size and
attack surface, and makes Linux distribution simpler.

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
sudo pacman -S --needed python python-pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
printwatch
```

The release workflow currently produces unsigned beta artifacts: a Windows installer and
portable ZIP, an Apple Silicon macOS app archive, and a Linux bundle. Windows signing and
macOS signing/notarization remain public-release gates. The Linux bundle builds successfully
on the CI target, but current CachyOS remains a required hands-on compatibility test.

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
- [`docs/ADR-0001-native-mjpeg.md`](docs/ADR-0001-native-mjpeg.md) — native stream-runtime decision and measured impact
- [`docs/MATRIX_INTEGRATION.md`](docs/MATRIX_INTEGRATION.md) — safe integration strategy
- [`SECURITY.md`](SECURITY.md) — vulnerability reporting and local-data model

## Why this exists

Phone apps are useful away from a desk, but makers often want a small desktop window beside
their slicer, terminal, or browser. PrintWatch was created to monitor an FDM printer and a
resin printer without repeatedly reaching for a phone or opening separate browser tabs.
