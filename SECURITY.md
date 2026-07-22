# Security Policy

## Supported versions

Security fixes are applied to the latest pre-release or stable line.

## Reporting a vulnerability

Open a private GitHub security advisory for this repository. Do not publish credentials,
private camera addresses, screenshots, diagnostics bundles, or exploit details in a public
issue.

## Security model

PrintWatch Desktop is local-first and has no telemetry, hosted account, or cloud relay. Camera
URLs and app preferences are stored in the user's platform-specific configuration directory.
Embedded URL credentials are rejected because the current configuration store is not a secrets
vault.

Application logs are local, rotate at 1 MiB with three backups, and redact URLs, IPv4/IPv6
addresses, and the user's home-directory path. Application event code records camera IDs and
connection kinds rather than stream URLs.

The diagnostics exporter creates a reviewable ZIP containing app/platform metadata, redacted
configuration facts, and a sanitized tail of the local log. It omits camera names, hosts,
addresses, notes, query strings, credentials, screenshots, and nonstandard endpoint paths.
Users should still review every diagnostics bundle before sharing it.

HTTP camera streams are not encrypted. Use them only on a trusted local network or through a
VPN you control. Do not expose a printer camera port directly to the public internet.

The application is a monitoring convenience, not a fire, motion, electrical, ventilation, or
resin-safety system. Users remain responsible for safe printer operation.
