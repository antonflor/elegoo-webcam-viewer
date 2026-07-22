# Public Release Plan

## Current readiness assessment

The original prototype was approximately **20–25% of a public desktop product**: the core idea
worked, but it supported only one URL, used a fixed window, had no tests or CI, and distributed
an unsigned 190 MB one-file executable. The repository foundation in `v0.1.0-alpha` moves the
project to roughly **55–60% of an honest beta**. It is not yet a stable public release.

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
- [ ] GUI smoke tests on all three operating systems
- [ ] Eight-hour two-printer soak test
- [ ] Offline/reconnect test
- [ ] Upgrade and corrupted-config test on packaged builds
- [ ] Accessibility review

### Windows

- [x] Automated PyInstaller build design
- [x] Inno Setup installer definition
- [ ] Clean Windows 11 installation test
- [ ] Microsoft code-signing certificate and signed installer
- [ ] SmartScreen reputation plan
- [ ] Portable ZIP validation

### macOS Apple Silicon

- [x] Native PyInstaller build design
- [ ] Apple Developer ID certificate
- [ ] Hardened runtime and entitlements validation
- [ ] Notarization and stapling
- [ ] Clean Apple Silicon installation test
- [ ] Camera test on macOS 14+

### Linux / CachyOS

- [x] Source-install instructions
- [x] Linux native bundle workflow
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
- [ ] Release checksums and provenance attestation

### Portfolio and launch

- [ ] Product icon and screenshots
- [ ] 30–60 second demo video/GIF
- [ ] Hardware compatibility table
- [ ] Public roadmap/issues
- [ ] Release announcement and portfolio case study

## Test hardware matrix

| Platform | Required device | Status |
|---|---|---|
| Windows 11 x64 | User's main Windows workstation | Pending |
| macOS 14+ arm64 | Apple Silicon Mac | Pending |
| CachyOS current | x64 PC/VM | Pending |
| Printer A | User's FDM printer/camera | Pending model and soak test |
| Printer B | User's resin printer/camera | Pending model and soak test |

## Version strategy

- `0.1.x`: core camera management and build pipeline
- `0.2.x`: hardware beta, diagnostics, reconnection
- `0.3.x`: grid view and UX polish
- `0.9.x`: signed release candidates
- `1.0.0`: stable public release

## Immediate next work

1. Run CI and correct platform-specific failures.
2. Add connection probing and structured logs.
3. Confirm the exact FDM and resin printer models and stream URLs during hardware testing.
4. Produce unsigned beta artifacts from a tagged release.
5. Test on Windows, Apple Silicon, and CachyOS before claiming compatibility.
