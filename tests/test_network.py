"""Integration tests: real Qt networking against a local camera server."""

from __future__ import annotations

from printwatch.probe import CameraProbe
from printwatch.stream import MjpegViewer
from printwatch.theme import StreamState


def test_viewer_shows_live_mjpeg_stream(qapp, camera_server, wait_until) -> None:
    viewer = MjpegViewer()
    states: list[str] = []
    viewer.state_changed.connect(states.append)
    viewer.start(f"{camera_server}/video")
    try:
        assert wait_until(lambda: viewer.has_frame)
        assert viewer.state == StreamState.LIVE
        assert viewer.frame_size.width() == 64
        assert states[:2] == [StreamState.CONNECTING.value, StreamState.LIVE.value]
    finally:
        viewer.stop(clear_frame=True)


def test_viewer_refreshes_jpeg_snapshot_endpoint(qapp, camera_server, wait_until) -> None:
    viewer = MjpegViewer()
    viewer.start(f"{camera_server}/snapshot")
    try:
        assert wait_until(lambda: viewer.has_frame)
        assert viewer.state == StreamState.LIVE
    finally:
        viewer.stop(clear_frame=True)


def test_switching_camera_clears_previous_frame(qapp, camera_server, wait_until) -> None:
    viewer = MjpegViewer()
    viewer.start(f"{camera_server}/video")
    try:
        assert wait_until(lambda: viewer.has_frame)
        viewer.start(f"{camera_server}/missing")
        assert not viewer.has_frame
        assert wait_until(lambda: viewer.state == StreamState.OFFLINE)
        assert not viewer.has_frame
    finally:
        viewer.stop(clear_frame=True)


def test_reconnect_to_same_camera_keeps_last_frame(qapp, camera_server, wait_until) -> None:
    viewer = MjpegViewer()
    viewer.start(f"{camera_server}/video")
    try:
        assert wait_until(lambda: viewer.has_frame)
        viewer.reload()
        assert viewer.has_frame
        assert viewer.state == StreamState.RECONNECTING
    finally:
        viewer.stop(clear_frame=True)


def _probe(url: str, wait_until) -> tuple[bool, str]:
    probe = CameraProbe()
    results: list[tuple[bool, str]] = []
    probe.completed.connect(lambda ok, message: results.append((ok, message)))
    probe.start(url, timeout_ms=3_000)
    assert wait_until(lambda: bool(results), timeout=6)
    assert len(results) == 1
    return results[0]


def test_probe_passes_for_mjpeg_stream(qapp, camera_server, wait_until) -> None:
    ok, message = _probe(f"{camera_server}/video", wait_until)
    assert ok
    assert "valid camera frame" in message


def test_probe_passes_for_snapshot(qapp, camera_server, wait_until) -> None:
    ok, _ = _probe(f"{camera_server}/snapshot", wait_until)
    assert ok


def test_probe_fails_for_html_dashboard(qapp, camera_server, wait_until) -> None:
    ok, message = _probe(f"{camera_server}/not-a-camera", wait_until)
    assert not ok
    assert "JPEG" in message


def test_probe_fails_for_missing_endpoint(qapp, camera_server, wait_until) -> None:
    ok, _ = _probe(f"{camera_server}/missing", wait_until)
    assert not ok


def test_unreachable_camera_stays_offline_while_retrying(qapp, camera_server, wait_until) -> None:
    viewer = MjpegViewer()
    states: list[str] = []
    viewer.state_changed.connect(states.append)
    viewer.start(f"{camera_server}/missing")
    try:
        assert wait_until(lambda: viewer.state == StreamState.OFFLINE)
        viewer.reload()  # what the backoff timer does
        assert viewer.state == StreamState.OFFLINE
        assert states == [StreamState.CONNECTING.value, StreamState.OFFLINE.value]
    finally:
        viewer.stop(clear_frame=True)
