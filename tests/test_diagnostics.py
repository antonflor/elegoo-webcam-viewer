import json
from pathlib import Path
from zipfile import ZipFile

from printwatch.diagnostics import export_diagnostics, redact_text, redacted_state
from printwatch.models import AppState, CameraProfile


def test_redacted_state_omits_sensitive_camera_fields() -> None:
    state = AppState(
        cameras=[
            CameraProfile(
                name="Secret Resin Room",
                url="http://192.168.50.44:3031/video?token=secret",
                notes="Garage printer password is not-for-sharing",
            )
        ]
    )
    payload = json.dumps(redacted_state(state))
    assert "Secret Resin Room" not in payload
    assert "192.168.50.44" not in payload
    assert "secret" not in payload
    assert "not-for-sharing" not in payload
    assert '"port": 3031' in payload
    assert '"path": "/video"' in payload


def test_redacted_state_hides_nonstandard_endpoint_paths() -> None:
    state = AppState(
        cameras=[CameraProfile(name="Printer", url="http://printer.local/private/token-123")]
    )
    payload = json.dumps(redacted_state(state))
    assert "token-123" not in payload
    assert "<redacted-path>" in payload


def test_redact_text_removes_urls_ipv4_and_ipv6() -> None:
    text = (
        "camera http://printer.local:3031/video failed at 192.168.1.20 and fe80::1ff:fe23:4567:890a"
    )
    redacted = redact_text(text)
    assert "printer.local" not in redacted
    assert "192.168.1.20" not in redacted
    assert "fe80::1ff:fe23:4567:890a" not in redacted


def test_export_bundle_contains_only_redacted_data(tmp_path: Path) -> None:
    log_path = tmp_path / "printwatch.log"
    log_path.write_text(
        "Failed http://10.0.0.8:3031/video from 10.0.0.8\n",
        encoding="utf-8",
    )
    state = AppState(
        cameras=[
            CameraProfile(
                name="Tony's FDM",
                url="http://10.0.0.8:3031/video?key=private",
                notes="Do not share this room name",
            )
        ]
    )
    destination_without_suffix = tmp_path / "diagnostics"
    destination = export_diagnostics(
        destination_without_suffix,
        state=state,
        app_version="0.2.0a2",
        log_path=log_path,
    )

    assert destination.suffix == ".zip"
    with ZipFile(destination) as archive:
        assert set(archive.namelist()) == {
            "README.txt",
            "printwatch-redacted.log",
            "state-redacted.json",
            "system.json",
        }
        combined = "\n".join(archive.read(name).decode("utf-8") for name in archive.namelist())

    for sensitive in (
        "Tony's FDM",
        "10.0.0.8",
        "private",
        "Do not share this room name",
    ):
        assert sensitive not in combined
