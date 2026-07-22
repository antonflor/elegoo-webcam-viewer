# Public Release Plan

## Current readiness assessment

The original prototype was approximately **20–25% of a public desktop product**: the core idea
worked, but it supported only one URL, used a fixed window, had no tests or CI, and distributed
an unsigned 190 MB one-file executable. The `v0.2.0a2` software now includes ordered
multi-camera management, a native MJPEG/JPEG runtime, connection probing, rotating privacy-safe
logs, redacted diagnostics, onboarding, nineteen tests, and validated cross-platform packaging.
This is roughly **80% of an honest public beta**, but it is not a stable `v1.0.0` release until
the remaining hands-on hardware, signing, installation, and accessibility gates pass.

## Build validation record

### Cross-platform packaging foundation

On July 22, 2026, GitHub Actions release run `29893266522` first completed the Windows x64,
Apple Silicon macOS, and Linux x64 packaging matrix using the WebEngine prototype runtime.

### Native MJPEG runtime

On July 22, 2026, GitHub Actions release run `29894865275` passed lint, formatting, thirteen
unit tests, source compilation, and all three native packaging jobs. Removing WebEngine reduced
the uploaded platform artifacts substantially:

| Platform artifact | WebEngine build | Native build | Reduction |
|---|---:|---:|---:|
| Windows x64 | 346.0 MB | 70.1 MB | 79.7% |
| Linux x64 | 224.4 MB | 73.1 MB | 67.4% |
| macOS arm64 | 167.4 MB | 28.1 MB | 83.2% |

### Beta operations

The `v0.2.0a2` gate adds privacy-focused diagnostics, local log redaction, independent camera
probing, camera enable/disable and reordering, and first-run onboarding. The final PR matrix
must pass nineteen tests and rebuild all three platform artifacts before merge.

The publication job remains tag-only. Artifact creation proves the packaging pipeline, but not
clean installation, runtime printer compatibility, signing, accessibility, or long-duration
stability.

## Required release gates

### Product

- [x] Multiple named cameras
- [x] Automatic camera cycling
- [x] Local state persistence
- [x] Original-frame screenshots and always-on-top behavior
- [x] Native MJPEG/JPEG viewer with bounded reconnect behavior
- [x] About/privacy/trademark/safety screen
- [x] Enable/disable and reorder UI
- [x] Connection test with timeout and valid-frame verification
- [x] Redacted diagnostics export and rotating local logs
- [x] First-run onboarding
- [ ] Grid view or explicit decision to defer it from `v1.0`

### Quality

- [x] Domain, persistence, parser, redaction, diagnostics, and logging tests
- [x] Ruff, formatting, pytest, and source-compilation CI
- [x] Native packaging jobs execute successfully on all three CI targets
- [x] Reconnect state machine implemented with bounded backoff
- [x] Sensitive-value fixtures are absent from exported diagnostics
- [ ] GUI smoke tests on all three operating systems
- [ ] Eight-hour two-printer soak test
- [ ] Physical offline/disconnect/reconnect test
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
- [x] WebEngine/Chromium sandbox dependency removed
- [ ] Test current CachyOS in a clean VM or physical host
- [ ] Validate native Qt Network bundle with live streams on CachyOS
- [ ] Choose and test AppImage/AUR/Flatpak packaging
- [ ] Desktop icon and menu integration

### Security and legal

- [x] MIT license
- [x] Trademark/non-affiliation statement
- [x] Local-only and no-telemetry scope
- [x] Credentials rejected in URL configuration
- [x] URL, IP, and home-directory log redaction
- [x] Diagnostics omit names, hosts, notes, query strings, credentials, and screenshots
- [x] Tagged release workflow generates checksums and provenance attestations
- [ ] Dependency license inventory
- [ ] Threat-model review
- [ ] Vulnerability reporting address confirmed
- [ ] Validate checksums and attestations on the first tagged prerelease

### Portfolio and launch

- [ ] Product icon and screenshots
- [ ] 30–60 second demo video/GIF
- [ ] Hardware compatibility table
- [ ] Public roadmap/issues
- [ ] Release announcement and portfolio case study

## Test hardware matrix

| Platform | Required device | Status |
|---|---|---|
| Windows 11 x64 | Windows workstation | Native CI build passed; clean install pending |
| macOS 14+ arm64 | Apple Silicon Mac | Native CI build passed; clean install pending |
| CachyOS current | x64 PC or VM | Native Linux build passed; CachyOS test pending |
| Printer A | FDM printer and camera | Pending model and eight-hour soak test |
| Printer B | Resin printer and camera | Pending model and eight-hour soak test |

## Version strategy

- `0.1.x`: core camera management and build pipeline
- `0.2.x`: native runtime, hardware beta, diagnostics, and reconnection
- `0.3.x`: grid view and UX polish
- `0.9.x`: signed release candidates
- `1.0.0`: stable public release

## Immediate next work

1. Install the unsigned beta on Windows, Apple Silicon, and CachyOS and record results.
2. Confirm the exact FDM and resin printer models and stream URLs in the compatibility table.
3. Run an eight-hour two-camera soak test with disconnect and reconnect scenarios.
4. Decide whether grid view is a `v1.0` requirement or a post-launch feature.
5. Add the product icon, screenshots, accessibility polish, and signing configuration.
6. Complete dependency-license and threat-model review before the release candidate.
