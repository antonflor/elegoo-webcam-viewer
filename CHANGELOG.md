# Changelog

All notable changes are documented here. The project follows Semantic Versioning once stable.

## [Unreleased]

## [0.3.0a1] - 2026-10-30

### Added

- Dark theme, app icon, and redesigned main window: camera header with a Live / Connecting /
  Offline badge, resolution and frame rate, sidebar status dots, and a first-run empty state.
- Next/previous camera shortcuts (Ctrl+Tab / Ctrl+Shift+Tab) and shortcuts for auto-cycle and
  pin-to-top; toolbar tooltips list each shortcut.
- `scripts/demo_camera.py`: simulated FDM, resin, and snapshot cameras for development and demos.
- `scripts/build_icons.py` and Windows/macOS icons for packaged builds and the installer.
- Integration tests that exercise the stream viewer, connection test, dialogs, and main window
  against a local camera server.

### Changed

- Switched from PyQt6 (GPLv3) to PySide6-Essentials (LGPLv3) so MIT-licensed binaries can be
  distributed; packaged Windows build shrank from 113 MB to 94 MB.
- Manual camera switches restart the auto-cycle countdown.
- Screenshots default to the operating system's Pictures folder.
- The Windows installer file name and version now follow the app version.
- CI installs the Qt runtime libraries and runs GUI tests headlessly.

### Fixed

- Switching to an unreachable camera kept showing the previous camera's last frame.
- An offline camera flickered between "Connecting" and "Offline" while retrying.
- The startup "ready" message hid the first camera's connection status.
- Editing a camera restarted its stream twice.
- The HTTP User-Agent reported a stale version.

### Added

- Multi-camera profile management.
- Configurable automatic camera cycling.
- Camera enable/disable controls and user-defined cycle ordering.
- Independent camera connection testing that waits for a valid JPEG frame.
- First-run onboarding for adding the initial printer camera.
- Local atomic state persistence and corrupt-state recovery.
- Bounded rotating application logs with privacy redaction.
- Redacted diagnostics ZIP export for support and troubleshooting.
- Cross-platform package layout and build workflows.
- Product SDD, release plan, Matrix integration strategy, and security policy.
- Native MJPEG/JPEG frame parsing and automatic reconnect with bounded backoff.
- About dialog with privacy, trademark, and safety positioning.
- Validation for malformed or out-of-range stream URL ports.

### Changed

- Product identity moved from an ELEGOO-specific prototype to independent PrintWatch Desktop.
- Window is resizable and no longer tied to one hard-coded URL.
- Camera rendering now uses Qt Network instead of an embedded Chromium/WebEngine process.
- Screenshots save the original received camera frame rather than a rendered browser surface.
- Diagnostics omit camera names, hosts, addresses, notes, query strings, credentials,
  screenshots, and nonstandard endpoint paths.

### Removed

- PyQt6-WebEngine and its bundled Chromium runtime.

## [0.0.1] - 2026-07-21

### Added

- Original single-stream Windows prototype with screenshot and always-on-top controls.
