"""Smoke tests for the main window using an isolated state file and settings."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from printwatch.app import PrintWatchWindow
from printwatch.models import AppPreferences, AppState, CameraProfile
from printwatch.storage import StateRepository
from printwatch.theme import StreamState, apply_theme


@pytest.fixture
def make_window(qapp, tmp_path: Path):
    apply_theme(qapp)
    windows: list[PrintWatchWindow] = []

    def _make(state: AppState) -> PrintWatchWindow:
        repository = StateRepository(tmp_path / "state.json")
        repository.save(state)
        settings = QSettings(str(tmp_path / "window.ini"), QSettings.Format.IniFormat)
        window = PrintWatchWindow(repository=repository, settings=settings)
        windows.append(window)
        return window

    yield _make
    for window in windows:
        window.close()
        window.deleteLater()
    qapp.processEvents()


def test_empty_state_offers_first_camera(make_window) -> None:
    window = make_window(AppState(preferences=AppPreferences(onboarding_completed=True)))
    assert window.viewer_stack.currentWidget() is window.empty_state
    assert window.empty_state.button.text() == "Add your first camera"
    assert not window.edit_action.isEnabled()
    assert not window.cycle_action.isEnabled()


def test_disabled_cameras_point_to_manager(make_window) -> None:
    camera = CameraProfile(name="Off", url="http://127.0.0.1:9/video", enabled=False)
    window = make_window(AppState(cameras=[camera]))
    assert window.viewer_stack.currentWidget() is window.empty_state
    assert window.empty_state.button.text() == "Manage cameras"
    assert window.manage_action.isEnabled()


def test_selected_camera_streams_and_cycles(make_window, camera_server, wait_until) -> None:
    cameras = [
        CameraProfile(name="FDM", url=f"{camera_server}/video", id="fdm"),
        CameraProfile(name="Resin", url=f"{camera_server}/snapshot", id="resin"),
    ]
    window = make_window(
        AppState(
            cameras=cameras,
            preferences=AppPreferences(selected_camera_id="fdm", onboarding_completed=True),
        )
    )
    assert window.current_camera_id() == "fdm"
    assert window.header.title.text() == "FDM"
    assert wait_until(lambda: window.viewer.state == StreamState.LIVE)
    assert window.screenshot_action.isEnabled()
    assert window.cycle_action.isEnabled()

    window.select_next_camera()
    assert window.current_camera_id() == "resin"
    assert window.repository.load().preferences.selected_camera_id == "resin"
    window.select_previous_camera()
    assert window.current_camera_id() == "fdm"


def test_screenshot_saves_original_frame(make_window, camera_server, wait_until, tmp_path):
    camera = CameraProfile(name="FDM", url=f"{camera_server}/video", id="fdm")
    window = make_window(AppState(cameras=[camera]))
    assert wait_until(lambda: window.viewer.has_frame)
    destination = tmp_path / "frame.png"
    assert window.viewer.save_current_frame(str(destination))
    assert destination.stat().st_size > 0
