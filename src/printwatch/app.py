from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QSettings, Qt, QTimer
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from printwatch import __version__
from printwatch.dialogs import CameraDialog, CycleIntervalDialog
from printwatch.models import CameraProfile
from printwatch.storage import StateRepository
from printwatch.stream import MjpegViewer


class PrintWatchWindow(QMainWindow):
    def __init__(self, repository: StateRepository | None = None) -> None:
        super().__init__()
        self.repository = repository or StateRepository()
        self.state = self.repository.load()
        self.window_settings = QSettings("Monty Labs", "PrintWatch Desktop")

        self.setWindowTitle(f"PrintWatch Desktop {__version__}")
        self.setMinimumSize(820, 520)
        self.resize(1100, 700)
        geometry = self.window_settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        self.camera_list = QListWidget()
        self.camera_list.setMinimumWidth(210)
        self.camera_list.currentItemChanged.connect(self._camera_selection_changed)

        self.empty_label = QLabel(
            "<h2>No cameras configured</h2>"
            "<p>Add an ELEGOO or direct HTTP/MJPEG camera stream to begin.</p>"
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setTextFormat(Qt.TextFormat.RichText)

        self.viewer = MjpegViewer()
        self.viewer.status_changed.connect(self.statusBar().showMessage)
        self.viewer.frame_received.connect(lambda _size: self.screenshot_action.setEnabled(True))

        self.viewer_stack = QStackedWidget()
        self.viewer_stack.addWidget(self.empty_label)
        self.viewer_stack.addWidget(self.viewer)

        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.addWidget(QLabel("<b>Cameras</b>"))
        sidebar_layout.addWidget(self.camera_list)

        splitter = QSplitter()
        splitter.addWidget(sidebar)
        splitter.addWidget(self.viewer_stack)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([230, 870])
        self.setCentralWidget(splitter)

        self._build_toolbar()
        self.cycle_timer = QTimer(self)
        self.cycle_timer.timeout.connect(self.select_next_camera)

        self._refresh_camera_list()
        self._restore_selection()
        self._sync_cycle_timer()
        self.statusBar().showMessage("Local-only camera viewer ready")

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(toolbar)

        self.add_action = QAction("Add", self)
        self.add_action.setShortcut(QKeySequence.StandardKey.New)
        self.add_action.triggered.connect(self.add_camera)
        toolbar.addAction(self.add_action)

        self.edit_action = QAction("Edit", self)
        self.edit_action.setShortcut(QKeySequence("Ctrl+E"))
        self.edit_action.triggered.connect(self.edit_camera)
        toolbar.addAction(self.edit_action)

        self.remove_action = QAction("Remove", self)
        self.remove_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.remove_action.triggered.connect(self.remove_camera)
        toolbar.addAction(self.remove_action)

        toolbar.addSeparator()

        self.reload_action = QAction("Reconnect", self)
        self.reload_action.setShortcut(QKeySequence.StandardKey.Refresh)
        self.reload_action.triggered.connect(self.viewer.reload)
        toolbar.addAction(self.reload_action)

        self.screenshot_action = QAction("Screenshot", self)
        self.screenshot_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.screenshot_action.triggered.connect(self.take_screenshot)
        self.screenshot_action.setEnabled(False)
        toolbar.addAction(self.screenshot_action)

        self.pin_action = QAction("Pin to top", self)
        self.pin_action.setCheckable(True)
        self.pin_action.toggled.connect(self.toggle_always_on_top)
        toolbar.addAction(self.pin_action)

        toolbar.addSeparator()

        self.cycle_action = QAction("Cycle cameras", self)
        self.cycle_action.setCheckable(True)
        self.cycle_action.setChecked(self.state.preferences.cycle_enabled)
        self.cycle_action.toggled.connect(self.toggle_cycle)
        toolbar.addAction(self.cycle_action)

        self.cycle_interval_action = QAction(
            f"Every {self.state.preferences.cycle_interval_seconds}s", self
        )
        self.cycle_interval_action.triggered.connect(self.change_cycle_interval)
        toolbar.addAction(self.cycle_interval_action)

        toolbar.addSeparator()
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)

    def _refresh_camera_list(self) -> None:
        selected_id = self.current_camera_id()
        self.camera_list.clear()
        for camera in self.state.cameras:
            if not camera.enabled:
                continue
            item = QListWidgetItem(camera.name)
            item.setData(Qt.ItemDataRole.UserRole, camera.id)
            item.setToolTip(camera.url)
            self.camera_list.addItem(item)
            if camera.id == selected_id:
                self.camera_list.setCurrentItem(item)

        has_cameras = self.camera_list.count() > 0
        self.viewer_stack.setCurrentWidget(self.viewer if has_cameras else self.empty_label)
        self._set_camera_actions_enabled(has_cameras)

    def _restore_selection(self) -> None:
        preferred_id = self.state.preferences.selected_camera_id
        for index in range(self.camera_list.count()):
            item = self.camera_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == preferred_id:
                self.camera_list.setCurrentRow(index)
                return
        if self.camera_list.count():
            self.camera_list.setCurrentRow(0)

    def _set_camera_actions_enabled(self, enabled: bool) -> None:
        self.edit_action.setEnabled(enabled)
        self.remove_action.setEnabled(enabled)
        self.reload_action.setEnabled(enabled)
        self.screenshot_action.setEnabled(enabled and self.viewer.has_frame)
        self.cycle_action.setEnabled(self.camera_list.count() > 1)

    def current_camera_id(self) -> str | None:
        item = self.camera_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def current_camera(self) -> CameraProfile | None:
        camera_id = self.current_camera_id()
        return next((camera for camera in self.state.cameras if camera.id == camera_id), None)

    def _camera_selection_changed(self, current: QListWidgetItem | None, _previous) -> None:
        if current is None:
            return
        camera_id = current.data(Qt.ItemDataRole.UserRole)
        camera = next((item for item in self.state.cameras if item.id == camera_id), None)
        if camera is None:
            return
        self.state.preferences.selected_camera_id = camera.id
        self.repository.save(self.state)
        self.viewer_stack.setCurrentWidget(self.viewer)
        self.screenshot_action.setEnabled(False)
        self.viewer.start(camera.url)
        self.setWindowTitle(f"{camera.name} — PrintWatch Desktop")

    def add_camera(self) -> None:
        dialog = CameraDialog(self)
        if dialog.exec() != CameraDialog.DialogCode.Accepted:
            return
        camera = dialog.profile()
        camera.validate()
        self.state.cameras.append(camera)
        self.state.preferences.selected_camera_id = camera.id
        self.repository.save(self.state)
        self._refresh_camera_list()
        self._restore_selection()
        self._sync_cycle_timer()

    def edit_camera(self) -> None:
        camera = self.current_camera()
        if camera is None:
            return
        dialog = CameraDialog(self, camera)
        if dialog.exec() != CameraDialog.DialogCode.Accepted:
            return
        updated = dialog.profile()
        updated.validate()
        index = self.state.cameras.index(camera)
        self.state.cameras[index] = updated
        self.repository.save(self.state)
        self._refresh_camera_list()
        self._restore_selection()
        self.viewer.start(updated.url)

    def remove_camera(self) -> None:
        camera = self.current_camera()
        if camera is None:
            return
        answer = QMessageBox.question(
            self,
            "Remove camera",
            f"Remove “{camera.name}” from PrintWatch?\n\nThis does not change the printer.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.state.cameras = [item for item in self.state.cameras if item.id != camera.id]
        self.state.preferences.selected_camera_id = None
        self.repository.save(self.state)
        self.viewer.stop(clear_frame=True)
        self._refresh_camera_list()
        self._restore_selection()
        self._sync_cycle_timer()

    def select_next_camera(self) -> None:
        count = self.camera_list.count()
        if count < 2:
            return
        next_row = (self.camera_list.currentRow() + 1) % count
        self.camera_list.setCurrentRow(next_row)

    def toggle_cycle(self, enabled: bool) -> None:
        self.state.preferences.cycle_enabled = enabled
        self.repository.save(self.state)
        self._sync_cycle_timer()

    def change_cycle_interval(self) -> None:
        dialog = CycleIntervalDialog(self, self.state.preferences.cycle_interval_seconds)
        if dialog.exec() != CycleIntervalDialog.DialogCode.Accepted:
            return
        self.state.preferences.cycle_interval_seconds = dialog.spin.value()
        self.repository.save(self.state)
        self.cycle_interval_action.setText(f"Every {dialog.spin.value()}s")
        self._sync_cycle_timer()

    def _sync_cycle_timer(self) -> None:
        should_run = self.state.preferences.cycle_enabled and self.camera_list.count() > 1
        if should_run:
            self.cycle_timer.start(self.state.preferences.cycle_interval_seconds * 1000)
        else:
            self.cycle_timer.stop()

    def toggle_always_on_top(self, enabled: bool) -> None:
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def take_screenshot(self) -> None:
        camera = self.current_camera()
        if camera is None:
            return
        pictures = Path(os.path.expanduser("~/Pictures"))
        if not pictures.exists():
            pictures = Path.home()
        safe_name = "".join(character if character.isalnum() else "_" for character in camera.name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suggested = pictures / f"{safe_name}_{timestamp}.png"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save camera screenshot", str(suggested), "PNG image (*.png);;JPEG image (*.jpg)"
        )
        if not path:
            return
        if not self.viewer.save_current_frame(path):
            QMessageBox.warning(
                self,
                "Screenshot unavailable",
                "PrintWatch has not received a camera frame yet.",
            )

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "About PrintWatch Desktop",
            f"<h2>PrintWatch Desktop {__version__}</h2>"
            "<p>A local-first, multi-camera monitor for 3D printers.</p>"
            "<p>No account, cloud service, or telemetry is required.</p>"
            "<p><b>Independent project:</b> not affiliated with or endorsed by ELEGOO. "
            "ELEGOO and Matrix are trademarks of their respective owners.</p>"
            "<p>This application is a monitoring convenience, not a printer safety system.</p>",
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self.viewer.stop()
        self.window_settings.setValue("geometry", self.saveGeometry())
        self.repository.save(self.state)
        super().closeEvent(event)


def main() -> int:
    QApplication.setOrganizationName("Monty Labs")
    QApplication.setApplicationName("PrintWatch Desktop")
    QApplication.setApplicationVersion(__version__)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    window = PrintWatchWindow()
    window.show()
    return app.exec()
