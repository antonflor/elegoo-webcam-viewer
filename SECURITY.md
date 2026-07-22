# Security Policy

## Supported versions

Security fixes are applied to the latest pre-release or stable line.

## Reporting a vulnerability

Open a private GitHub security advisory for this repository. Do not publish credentials,
private camera addresses, screenshots, or exploit details in a public issue.

## Security model

PrintWatch Desktop is local-first and has no telemetry or cloud service. Camera URLs and app
preferences are stored in the user's platform-specific configuration directory. Embedded URL
credentials are rejected because the current configuration store is not a secrets vault.

HTTP camera streams are not encrypted. Use them only on a trusted local network or through a
VPN you control. Do not expose a printer camera port directly to the public internet.

The application is a monitoring convenience, not a fire, motion, electrical, ventilation, or
resin-safety system. Users remain responsible for safe printer operation.
