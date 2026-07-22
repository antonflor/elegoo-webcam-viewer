from __future__ import annotations

import json
import platform
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

from printwatch.models import AppState

_URL_PATTERN = re.compile(r"https?://[^\s\]\[(){}<>\"']+", re.IGNORECASE)
_IPV4_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_IPV6_PATTERN = re.compile(r"\b(?:[0-9A-Fa-f]{1,4}:){2,}[0-9A-Fa-f:]+\b")
_MAX_LOG_BYTES = 256 * 1024
_SAFE_ENDPOINT_PATHS = {"/", "/mjpeg", "/snapshot.jpg", "/stream", "/video"}


def redact_text(text: str) -> str:
    text = _URL_PATTERN.sub("<redacted-url>", text)
    text = _IPV4_PATTERN.sub("<redacted-ip>", text)
    return _IPV6_PATTERN.sub("<redacted-ip>", text)


def _redacted_endpoint_path(path: str) -> str:
    normalized = path or "/"
    return normalized if normalized in _SAFE_ENDPOINT_PATHS else "<redacted-path>"


def redacted_state(state: AppState) -> dict[str, object]:
    cameras: list[dict[str, object]] = []
    for index, camera in enumerate(state.cameras, start=1):
        parsed = urlsplit(camera.url)
        cameras.append(
            {
                "index": index,
                "kind": camera.kind.value,
                "enabled": camera.enabled,
                "scheme": parsed.scheme,
                "port": parsed.port,
                "path": _redacted_endpoint_path(parsed.path),
            }
        )

    return {
        "schema_version": state.schema_version,
        "camera_count": len(state.cameras),
        "enabled_camera_count": sum(camera.enabled for camera in state.cameras),
        "cycle_enabled": state.preferences.cycle_enabled,
        "cycle_interval_seconds": state.preferences.cycle_interval_seconds,
        "cameras": cameras,
    }


def system_report(app_version: str) -> dict[str, object]:
    return {
        "app_version": app_version,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "operating_system": platform.system(),
        "os_release": platform.release(),
        "machine": platform.machine(),
        "frozen_build": bool(getattr(sys, "frozen", False)),
    }


def _redacted_log_tail(log_path: Path | None) -> str:
    if log_path is None or not log_path.exists():
        return "No application log was available.\n"

    with log_path.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        handle.seek(max(0, size - _MAX_LOG_BYTES))
        raw = handle.read()
    return redact_text(raw.decode("utf-8", errors="replace"))


def export_diagnostics(
    destination: Path,
    *,
    state: AppState,
    app_version: str,
    log_path: Path | None = None,
) -> Path:
    if destination.suffix.lower() != ".zip":
        destination = destination.with_suffix(".zip")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, mode="w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "system.json",
            json.dumps(system_report(app_version), indent=2, sort_keys=True) + "\n",
        )
        archive.writestr(
            "state-redacted.json",
            json.dumps(redacted_state(state), indent=2, sort_keys=True) + "\n",
        )
        archive.writestr("printwatch-redacted.log", _redacted_log_tail(log_path))
        archive.writestr(
            "README.txt",
            "PrintWatch Desktop diagnostics\n\n"
            "This bundle omits camera names, hosts, IP addresses, notes, query strings, "
            "screenshots, credentials, and nonstandard endpoint paths. Review the files "
            "before sharing them.\n",
        )
    return destination
