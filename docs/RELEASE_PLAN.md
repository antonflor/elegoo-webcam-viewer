# Public Release Plan

## Current readiness assessment

The original prototype was approximately **20–25% of a public desktop product**: the core idea
worked, but it supported only one URL, used a fixed window, had no tests or CI, and distributed
an unsigned 190 MB one-file executable. The `v0.1.0-alpha` foundation, green CI, and successful
native artifact builds move the project to roughly **60–65% of an honest beta**. It is not yet
a stable public release.

## Build validation record

On July 22, 2026, GitHub Actions release run `29893266522` completed successfully for all
non-publishing jobs:

- Windows x64 portable ZIP and Inno Setup installer
- Apple Silicon macOS application archive
- Linux x64 application bundle
- Shared lint, formatting, unit-test, and source-compilation gate

The publication job was skipped as intended because the build did not use a version tag.
Artifact creation proves the packaging pipeline, but not clean installation, runtime camera
compatibility, signing, or long-duration stability.

## Required release gates

### Product

- [x] Multiple named cameras
- [x] Automatic camera cycling
- [x] Local state persistence
- [x] Screenshot and always-on-top behavior
- [ ] Enable/disable and reorder UI
- [ ] Connection test with timeout and useful diagnostics
- [ ] Grid view or explicit decision to defer it
- [ ] First-run onboarding
- [ ] About/privacy/trademark screens

### Quality

- [x] Domain and persistence unit tests
- [x] Ruff and pytest CI
- [x] Native packaging jobs execute successfully on all three CI targets
- [ ] GUI smoke tests on all three operating systems
- [ ] Eight-hour two-printer soak test
- [ ] Offline/reconnect test
- [ ] Upgrade and corrupted-config test on packaged builds
- [ ] Accessibility review

### Windows

- [x] Automated PyInstaller build
- [x] Inno Setup installer build
- [x] Portable ZIP artifact build
- [ ] Clean Windows 11 installation test
- [ ] Signed installer
- [ ] SmartScreen reputation plan

### macOS Apple Silicon

- [x] Native PyInstaller app build
- [x] Apple Silicon application archive build
- [ ] Signed application
- [ ] Hardened runtime validation
- [ ] Notarization and stapling
- [ ] Clean Apple Silicon installation test
- [ ] Camera test on macOS 14+

### Linux / CachyOS

- [x] Source-install instructions
- [x] Linux native bundle build
- [ ] Test current CachyOS in a clean VM or physical host
- [ ] Validate Qt WebEngine sandbox behavior
- [ ] Choose and test AppImage/AUR/Flatpak packaging
- [ ] Desktop icon and menu integration

### Security and legal

- [x] MIT license
- [x] Trademark/non-affiliation statement
- [x] Local-only and no-telemetry scope
- [x] Credentials rejected in URL configuration
- [ ] Dependency license inventory
- [ ] Threat-model review
- [ ] Vulnerability reporting address confirmed
- [ ] Tagged-release checksums and provenance attestation

### Portfolio and launch

- [ ] Product icon and screenshots
- [ ] 30–60 second demo video/GIF
- [ ] Hardware compatibility table
- [ ] Public roadmap/issues
- [ ] Release announcement and portfolio case study

## Test hardware matrix

| Platform | Required device | Status |
|---|---|---|
| Windows 11 x64 | Windows workstation | CI build passed; clean install pending |
| macOS 14+ arm64 | Apple Silicon Mac | CI build passed; clean install pending |
| CachyOS current | x64 PC or VM | Linux CI build passed; CachyOS test pending |
| Printer A | FDM printer and camera | Pending model and soak test |
| Printer B | Resin printer and camera | Pending model and soak test |

## Version strategy

- `0.1.x`: core camera management and build pipeline
- `0.2.x`: hardware beta, diagnostics, reconnection
- `0.3.x`: grid view and UX polish
- `0.9.x`: signed release candidates
- `1.0.0`: stable public release

## Immediate next work

1. Add connection probing, reconnection behavior, and structured local logs.
2. Confirm the exact FDM and resin printer models and stream URLs during hardware testing.
3. Install the unsigned beta on Windows, Apple Silicon, and CachyOS and record results.
4. Run an eight-hour two-camera soak test with disconnect and reconnect scenarios.
5. Add the product icon, screenshots, onboarding, and accessibility polish.
6. Complete signing requirements before broad distribution.
