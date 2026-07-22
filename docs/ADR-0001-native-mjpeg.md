# ADR-0001: Use a Native MJPEG Runtime

- **Status:** Accepted and validated
- **Date:** 2026-07-22
- **Decision owners:** PrintWatch maintainers

## Context

The original prototype displayed a camera URL in `QWebEngineView`. That made arbitrary browser
content easy to render, but embedded a complete Chromium runtime in every package. The first
validated builds were approximately 167 MB for the macOS artifact, 224 MB for Linux, and
346 MB for the combined Windows artifact archive. WebEngine also introduced a separate
renderer process, sandbox considerations, a larger dependency and security surface, and more
complex Linux compatibility.

The known ELEGOO camera use case is a direct MJPEG endpoint such as
`http://<printer-ip>:3031/video`. PrintWatch does not need JavaScript or a full web platform to
render that stream.

## Decision

PrintWatch uses Qt Network to read direct HTTP/HTTPS MJPEG or JPEG endpoints and a small,
bounded parser to extract JPEG frames. The application keeps only one active network stream
and one decoded source frame at a time.

The initial public protocol contract is intentionally narrow:

- Direct MJPEG streams
- Direct JPEG snapshot endpoints
- HTTP or HTTPS transport
- No credentials embedded in the URL

HTML dashboards, HLS, WebRTC, and RTSP are not part of this runtime. Future protocols must be
implemented as explicit, testable provider/viewer adapters rather than by restoring a general
embedded browser.

## Consequences

### Positive

- Removes PyQt6-WebEngine and bundled Chromium.
- Reduces package size, startup overhead, and attack surface.
- Avoids renderer-process crashes and Linux WebEngine sandbox concerns.
- Captures screenshots from the original camera frame.
- Makes reconnect behavior and connection errors application-controlled.

### Negative

- Camera web dashboards no longer render.
- Uncommon stream formats need explicit adapters.
- The MJPEG parser and reconnect state machine become project-owned code and require tests.

## Validation

GitHub Actions run `29894865275` passed lint, formatting, thirteen tests, source compilation,
and native packaging on Windows x64, Apple Silicon macOS, and Linux x64.

| Platform artifact | WebEngine build | Native build | Reduction |
|---|---:|---:|---:|
| Windows x64 | 346.0 MB | 70.1 MB | 79.7% |
| Linux x64 | 224.4 MB | 73.1 MB | 67.4% |
| macOS arm64 | 167.4 MB | 28.1 MB | 83.2% |

The pure frame parser is covered for chunk boundaries, multiple frames, multipart transport
headers, oversized incomplete frames, and split JPEG markers. Hardware-level stream and soak
testing remains part of the beta release gate.
