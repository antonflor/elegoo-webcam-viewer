# PrintWatch Desktop — Spec-Driven Development Plan

**Document status:** Active source of truth  
**Target release:** `v1.0.0` public release  
**Current implementation:** `v0.1.0-alpha`

## 1. Product statement

PrintWatch Desktop is a local-first, cross-platform desktop companion for people who operate
one or more 3D printers. It provides a compact, persistent way to view camera streams, switch
or cycle between printers, and capture evidence of a print without relying on a proprietary
mobile application.

The product begins with ELEGOO-compatible camera streams but remains vendor-neutral. It does
not claim to replace ELEGOO Matrix, a slicer, printer firmware, or a safety system.

## 2. Problem

A maker with an FDM printer and a resin printer currently has to use separate browser tabs,
a phone application, or manually replace one hard-coded camera URL. The original prototype
solves only one stream on one Windows computer and has no installer, release automation,
tests, compatibility contract, diagnostics, or public-support documentation.

## 3. Goals

1. Manage at least 20 named camera profiles and switch among them reliably.
2. Automatically cycle through enabled cameras at a user-defined interval.
3. Run on Windows 11, Apple Silicon macOS, and current CachyOS/Arch Linux.
4. Keep configuration and camera traffic local by default.
5. Provide reproducible builds, checksums, release notes, and a safe upgrade path.
6. Present a portfolio-quality user experience and repository.
7. Leave a clean adapter boundary for future documented printer-status integrations.

## 4. Non-goals for v1.0

- Cloud relay, remote access, NAT traversal, or hosted accounts.
- Uploading, slicing, or starting prints.
- Reimplementing the proprietary Matrix cloud service.
- Extracting Matrix tokens, intercepting app traffic, or relying on undocumented cloud APIs.
- AI failure detection or unattended safety guarantees.
- Storing usernames or passwords in the JSON configuration.

## 5. Users and primary scenarios

### Home maker

Runs two printers on the same LAN and keeps PrintWatch pinned beside a slicer. The app cycles
between both streams every 15 seconds and saves a screenshot when a print looks suspicious.

### Small print farm operator

Names several cameras, quickly selects a printer from the sidebar, and sees an actionable
connection error when a stream is offline.

### Cross-platform hobbyist

Uses the same camera configuration concepts on Windows, an Apple Silicon Mac, and CachyOS.

## 6. Functional requirements

### FR-1 Camera profiles

- Create, edit, remove, enable, and disable profiles.
- Required fields: stable ID, display name, stream URL, connection type.
- Accept `http://` and `https://` URLs.
- Reject embedded credentials until secure credential storage exists.
- Persist data locally and recover safely from a corrupt configuration.

**Acceptance:** Adding two valid URLs survives restart; deleting one never changes the printer.

### FR-2 Viewer

- Display the selected stream in an embedded browser surface.
- Support ELEGOO MJPEG streams using the known `:3031/video` pattern.
- Show connecting, loaded, and failed states.
- Reload manually and recover from a crashed renderer.

**Acceptance:** A disconnected printer produces a visible failure status without crashing.

### FR-3 Multi-camera navigation

- Show all enabled cameras in a sidebar.
- Preserve the selected camera across restart.
- Provide next-camera cycling for two or more cameras.
- Configure cycle intervals from 5 seconds through 60 minutes.
- Pause cycling automatically when fewer than two cameras are enabled.

**Acceptance:** With two cameras and a 5-second interval, selection alternates continuously.

### FR-4 Screenshots

- Capture the visible stream surface.
- Default to the user Pictures directory.
- Include camera name and timestamp in the suggested filename.
- Support PNG and JPEG.

### FR-5 Desktop behavior

- Resizable window with persisted geometry.
- Optional always-on-top behavior.
- Keyboard shortcuts for common actions.
- No mandatory account, analytics, or internet service.

### FR-6 Diagnostics (v0.2)

- Export a redacted diagnostics bundle with app version, OS, configuration schema, and recent
  local logs.
- Never include camera credentials or image data without explicit confirmation.

### FR-7 Grid view (v0.3)

- Optional 2-up and 4-up grid.
- Limit concurrently active browser surfaces to control memory use.
- Cycle mode remains available for low-resource systems.

## 7. Non-functional requirements

### Security and privacy

- Local-only by default; no telemetry in v1.0.
- Validate URLs before use.
- No embedded secrets in configuration.
- Atomic state writes and corrupt-state backup.
- Document that HTTP streams are unencrypted and should remain on trusted networks/VPNs.
- Publish SHA-256 checksums for release assets.

### Reliability

- Unit coverage for state validation, migration, and persistence.
- Renderer termination recovers without application exit.
- State format includes a schema version and migration strategy.

### Performance

- Idle memory target: under 350 MB with one active WebEngine stream.
- Startup target: under 5 seconds on supported hardware after first launch.
- UI interactions remain responsive when a camera is offline.

### Accessibility

- All actions keyboard reachable.
- Text labels do not rely on color alone.
- Minimum contrast and screen-reader labels reviewed before `v1.0.0`.

### Compatibility

- Windows 11 x64.
- macOS 14+ on Apple Silicon for the first signed macOS release.
- Current CachyOS/Arch Linux and Ubuntu LTS x64.
- Python 3.11 and 3.12 for source installs.

## 8. Architecture

```text
PyQt6 desktop shell
├── Main window and camera navigation
├── One active QWebEngineView (v0.1)
├── Dialogs and desktop actions
├── Domain model (no Qt dependency)
├── Atomic JSON state repository
└── Future provider adapters
    ├── Generic HTTP/MJPEG
    ├── Documented ELEGOO LAN APIs
    ├── Moonraker
    └── OctoPrint
```

The single active browser surface is deliberate: it supports cycling while avoiding one
Chromium renderer per configured printer. Grid view will introduce a bounded view pool.

## 9. Configuration contract

Default platform-specific location is selected by `platformdirs`.

```json
{
  "schema_version": 1,
  "cameras": [
    {
      "id": "uuid",
      "name": "FDM printer",
      "url": "http://192.168.1.50:3031/video",
      "kind": "elegoo_mjpeg",
      "enabled": true,
      "notes": ""
    }
  ],
  "preferences": {
    "cycle_enabled": true,
    "cycle_interval_seconds": 15,
    "selected_camera_id": "uuid"
  }
}
```

## 10. Packaging decision

- **Windows:** signed Inno Setup `.exe` installer plus portable ZIP.
- **macOS:** signed and notarized Apple Silicon `.app`, distributed as `.dmg` or zipped app.
- **Linux:** AppImage or self-contained tarball, plus an AUR packaging path for CachyOS.
- **Source:** Python package and tagged source archive.

A raw PyInstaller `.exe` is acceptable for alpha testing, but it is not the finished Windows
product. The current prototype is unusually large because Qt WebEngine includes Chromium and
because one-file mode embeds all dependencies. Public releases prefer an installer or an
on-directory portable bundle for faster startup and clearer provenance.

## 11. Release milestones

### M0 — Prototype audit (complete)

- Identify single hard-coded URL and Windows-only packaging.
- Preserve screenshot and always-on-top behavior.
- Establish independent-product naming and trademark disclaimer.

### M1 — Product foundation (`v0.1.0-alpha`)

- Package layout and versioning.
- Multi-camera CRUD.
- Automatic cycling.
- Atomic local state.
- Unit tests and linting.
- Cross-platform build workflow.
- SDD, security, contribution, and release documentation.

### M2 — Hardware beta (`v0.2.0`)

- Test one FDM and one resin ELEGOO printer.
- Add connection-test button and diagnostics export.
- Add structured local logs and redaction tests.
- Improve first-run onboarding and errors.
- Produce unsigned Windows/macOS/Linux beta assets.

### M3 — Experience beta (`v0.3.0`)

- Grid view.
- Camera reordering, enable/disable, and import/export.
- Tray/minimize behavior.
- Accessibility pass.
- Native icons and product screenshots.

### M4 — Release candidate (`v0.9.0`)

- Code signing and macOS notarization.
- Installer upgrades/uninstall tests.
- Clean-machine smoke tests.
- Dependency and license review.
- Threat model and privacy review.

### M5 — Public release (`v1.0.0`)

- All release gates green.
- Public repository, release notes, checksums, screenshots, and support templates.
- Stable configuration migration promise for the `1.x` line.

## 12. Open decisions

1. Final product icon and visual identity.
2. Whether Linux `v1.0` ships AppImage, Flatpak, AUR, or more than one.
3. Which exact printer models form the support matrix.
4. Whether a future signed build is published under Monty Labs or the individual developer.
5. Whether documented ELEGOO LAN control exists for each target model.

## 13. Definition of done for v1.0

A release is ready only when every required item in `docs/RELEASE_PLAN.md` is complete, two
real printers have passed a continuous eight-hour monitoring test, clean installations pass on
all supported operating systems, binaries are signed where applicable, and no critical/high
security defects remain open.
