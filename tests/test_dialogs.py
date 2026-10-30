from __future__ import annotations

from PySide6.QtCore import Qt

from printwatch.dialogs import CameraDialog, CameraManagerDialog, CycleIntervalDialog
from printwatch.models import CameraKind, CameraProfile


def test_camera_dialog_round_trips_profile(qapp) -> None:
    original = CameraProfile(
        name="Saturn", url="http://10.0.0.5/video", kind=CameraKind.ELEGOO_MJPEG, notes="Resin"
    )
    dialog = CameraDialog(profile=original)
    profile = dialog.profile()
    assert profile.id == original.id
    assert profile.kind == CameraKind.ELEGOO_MJPEG
    assert (profile.name, profile.url, profile.notes) == ("Saturn", original.url, "Resin")


def test_camera_dialog_rejects_invalid_url(qapp, monkeypatch) -> None:
    warnings: list[str] = []
    monkeypatch.setattr(
        "printwatch.dialogs.QMessageBox.warning",
        lambda _parent, _title, message: warnings.append(message),
    )
    dialog = CameraDialog()
    dialog.name_edit.setText("Printer")
    dialog.url_edit.setText("rtsp://10.0.0.5/stream")
    dialog._validate_and_accept()
    assert warnings and "http" in warnings[0]
    assert dialog.result() != CameraDialog.DialogCode.Accepted


def test_manager_reorders_and_disables(qapp) -> None:
    cameras = [CameraProfile(name=name, url=f"http://h/{name}") for name in ("A", "B", "C")]
    dialog = CameraManagerDialog(cameras)
    dialog.list_widget.setCurrentRow(2)
    dialog._move_current(-1)
    dialog.list_widget.item(0).setCheckState(Qt.CheckState.Unchecked)
    profiles = dialog.profiles()
    assert [profile.name for profile in profiles] == ["A", "C", "B"]
    assert [profile.enabled for profile in profiles] == [False, True, True]
    # The caller's list is untouched until the dialog is saved.
    assert all(camera.enabled for camera in cameras)


def test_cycle_interval_is_bounded(qapp) -> None:
    dialog = CycleIntervalDialog(current_seconds=1)
    assert dialog.spin.value() == 5
