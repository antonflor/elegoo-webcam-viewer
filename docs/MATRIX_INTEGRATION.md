# ELEGOO Matrix Integration Strategy

## What Matrix provides

ELEGOO describes Matrix as a mobile platform for batch device management, real-time monitoring,
remote parameter control, print history, alerts, and remote printing. Those capabilities span
local printer data and ELEGOO-operated cloud services.

## What PrintWatch can safely use

### Supported now

- Direct local HTTP/MJPEG camera streams exposed by a printer.
- User-supplied stream URLs.
- Local screenshots and camera cycling.

### Suitable future integrations

- Officially documented ELEGOO LAN endpoints or SDKs.
- Local status endpoints exposed by printer firmware.
- Exported print history files when documented and user-selected.
- Open integrations such as Moonraker or OctoPrint through explicit provider adapters.

### Explicitly out of scope

- Reading Matrix application files, tokens, cookies, or account credentials.
- Capturing/decrypting Matrix traffic to depend on undocumented cloud APIs.
- Impersonating the official app.
- Republishing proprietary assets or bundled code.
- Claiming remote-control safety without a documented and tested interface.

## Adapter boundary

A future provider interface should expose capabilities rather than vendor assumptions:

```python
class PrinterProvider(Protocol):
    def discover(self) -> list[PrinterDevice]: ...
    def camera_stream(self, device: PrinterDevice) -> StreamDescriptor: ...
    def status(self, device: PrinterDevice) -> PrinterStatus: ...
    def capabilities(self, device: PrinterDevice) -> set[Capability]: ...
```

Each provider must document authentication, transport security, firmware/model compatibility,
and whether commands are read-only or mutating.

## Recommended product sequence

1. Ship a reliable vendor-neutral multi-camera viewer.
2. Add read-only local printer status where an official/documented interface exists.
3. Add notifications and history only after data ownership and storage behavior are clear.
4. Consider print controls only as a separately reviewed feature with confirmations, audit logs,
   model-specific tests, and a prominent physical-safety warning.

## Trademark positioning

Use phrases such as “compatible with local camera streams used by selected ELEGOO printers.”
Do not use ELEGOO or Matrix as the product name, app icon, or visual identity. Keep the
non-affiliation statement visible in the README, About screen, and release descriptions.
