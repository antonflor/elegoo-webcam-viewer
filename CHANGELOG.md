# Changelog

All notable changes are documented here. The project follows Semantic Versioning once stable.

## [Unreleased]

### Added

- Multi-camera profile management.
- Configurable automatic camera cycling.
- Local atomic state persistence and corrupt-state recovery.
- Cross-platform package layout and build workflows.
- Product SDD, release plan, Matrix integration strategy, and security policy.
- Native MJPEG/JPEG frame parsing and automatic reconnect with bounded backoff.
- About dialog with privacy, trademark, and safety positioning.

### Changed

- Product identity moved from an ELEGOO-specific prototype to independent PrintWatch Desktop.
- Window is resizable and no longer tied to one hard-coded URL.
- Camera rendering now uses Qt Network instead of an embedded Chromium/WebEngine process.
- Screenshots save the original received camera frame rather than a rendered browser surface.

### Removed

- PyQt6-WebEngine and its bundled Chromium runtime.

## [0.0.1] - 2026-07-21

### Added

- Original single-stream Windows prototype with screenshot and always-on-top controls.
