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
from printwatch.diagnostics import export_diagnostics
from printwatch.dialogs import CameraDialog, CameraManagerDialog, CycleIntervalDialog
from printwatch.logging_config import configure_logging, get_logger
from printwatch.models import CameraProfile
from printwatch.probe import CameraProbe
from printwatch.storage import StateRepository
from printwatch.stream import MjpegViewer


class PrintWatchWindow(QMainWindow):
    def __init__(
        self,
        repository: StateRepository | None = None,
        log_path: Path | None = None,
    ) -> None:
        super().__init__()
        self.repository = repository or StateRepository()
        self.state = self.repository.load()
        self.log_path = log_path
        self.logger = get_logger("app")
        self.window_settings = QSettings("Monty Labs", "PrintWatch Desktop")
        self._probe_camera_id: str | None = None
        self._probe_camera_name = "Camera"

        self.setWindowTitle(f"PrintWatch Desktop {__version__}")
        self.setMinimumSize(820, 520)
        self.resize(1100, 700)
        geometry = self.window_settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        self.camera_list = QListWidget()
        self.camera_list.setMinimumWidth(210)
        self.camera_list.currentItemChanged.connect(self._camera_selection_changed)

        self.empty_label = QLabel()
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setTextFormat(Qt.TextFormat.RichText)

        self.viewer = MjpegViewer()
        self.viewer.status_changed.connect(self._viewer_status_changed)
        self.viewer.frame_received.connect(lambda _size: self.screenshot_action.setEnabled(True))

        self.probe = CameraProbe(self)
        self.probe.completed.connect(self._probe_completed)

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
        self.logger.info(
            "window initialized cameras=%d enabled=%d",
            len(self.state.cameras),
            sum(camera.enabled for camera in self.state.cameras),
        )
        QTimer.singleShot(0, self.show_onboarding_if_needed)

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

        self.manage_action = QAction("Manage", self)
        self.manage_action.setShortcut(QKeySequence("Ctrl+M"))
        self.manage_action.triggered.connect(self.manage_cameras)
        toolbar.addAction(self.manage_action)

        toolbar.addSeparator()

        self.test_action = QAction("Test", self)
        self.test_action.setShortcut(QKeySequence("Ctrl+T"))
        self.test_action.triggered.connect(self.test_camera)
        toolbar.addAction(self.test_action)

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

        diagnostics_action = QAction("Diagnostics", self)
        diagnostics_action.triggered.connect(self.export_diagnostics_bundle)
        toolbar.addAction(diagnostics_action)

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)

    def _refresh_camera_list(self) -> None:
        selected_id = self.state.preferences.selected_camera_id
        self.camera_list.clear()
        for camera in self.state.cameras:
            if not camera.enabled:
                continue
            item = QListWidgetItem(camera.name)
            item.setData(Qt.ItemDataRole.UserRole, camera.id)
            item.setToolTip("Direct local camera stream")
            self.camera_list.addItem(item)
            if camera.id == selected_id:
                self.camera_list.setCurrentItem(item)

        has_enabled_cameras = self.camera_list.count() > 0
        if has_enabled_cameras:
            self.viewer_stack.setCurrentWidget(self.viewer)
        else:
            if self.state.cameras:
                self.empty_label.setText(
                    "<h2>No cameras are enabled</h2>"
                    "<p>Use <b>Manage</b> to enable and reorder your printer cameras.</p>"
                )
            else:
                self.empty_label.setText(
                    "<h2>No cameras configured</h2>"
                    "<p>Add an ELEGOO or direct HTTP/MJPEG camera stream to begin.</p>"
                )
            self.viewer.stop(clear_frame=True)
            self.viewer_stack.setCurrentWidget(self.empty_label)
        self._set_camera_actions_enabled(has_enabled_cameras)

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
        self.test_action.setEnabled(enabled)
        self.reload_action.setEnabled(enabled)
        self.screenshot_action.setEnabled(enabled and self.viewer.has_frame)
        self.manage_action.setEnabled(bool(self.state.cameras))
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
        self.logger.info("camera selected id=%s kind=%s", camera.id, camera.kind.value)

    def _viewer_status_changed(self, status: str) -> None:
        self.statusBar().showMessage(status)

    def add_camera(self) -> None:
        dialog = CameraDialog(self)
        if dialog.exec() != CameraDialog.DialogCode.Accepted:
            return
        camera = dialog.profile()
        camera.validate()
        self.state.cameras.append(camera)
        self.state.preferences.selected_camera_id = camera.id
        self.state.preferences.onboarding_completed = True
        self.repository.save(self.state)
        self.logger.info("camera added id=%s kind=%s", camera.id, camera.kind.value)
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
        self.logger.info("camera edited id=%s kind=%s", updated.id, updated.kind.value)
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
        self.logger.info("camera removed id=%s", camera.id)
        self.viewer.stop(clear_frame=True)
        self._refresh_camera_list()
        self._restore_selection()
        self._sync_cycle_timer()

    def manage_cameras(self) -> None:
        dialog = CameraManagerDialog(self.state.cameras, self)
        if dialog.exec() != CameraManagerDialog.DialogCode.Accepted:
            return
        self.state.cameras = dialog.profiles()
        selected = next(
            (
                camera
                for camera in self.state.cameras
                if camera.id == self.state.preferences.selected_camera_id
            ),
            None,
        )
        if selected is None or not selected.enabled:
            self.state.preferences.selected_camera_id = None
            self.viewer.stop(clear_frame=True)
        self.repository.save(self.state)
        self.logger.info(
            "camera manager saved cameras=%d enabled=%d",
            len(self.state.cameras),
            sum(camera.enabled for camera in self.state.cameras),
        )
        self._refresh_camera_list()
        self._restore_selection()
        self._sync_cycle_timer()

    def test_camera(self) -> None:
        camera = self.current_camera()
        if camera is None:
            return
        self._probe_camera_id = camera.id
        self._probe_camera_name = camera.name
        self.test_action.setEnabled(False)
        self.statusBar().showMessage("Testing camera connection…")
        self.logger.info("camera probe started id=%s", camera.id)
        self.probe.start(camera.url)

    def _probe_completed(self, success: bool, message: str) -> None:
        self.test_action.setEnabled(self.current_camera() is not None)
        if success:
            self.logger.info("camera probe succeeded id=%s", self._probe_camera_id)
            QMessageBox.information(
                self,
                "Camera connection passed",
                f"{self._probe_camera_name}\n\n{message}",
            )
        else:
            self.logger.warning("camera probe failed id=%s", self._probe_camera_id)
            QMessageBox.warning(
                self,
                "Camera connection failed",
                f"{self._probe_camera_name}\n\n{message}",
            )
        self.statusBar().showMessage(message)
        self._probe_camera_id = None

    def select_next_camera(self) -> None:
        count = self.camera_list.count()
        if count < 2:
            return
        next_row = (self.camera_list.currentRow() + 1) % count
        self.camera_list.setCurrentRow(next_row)

    def toggle_cycle(self, enabled: bool) -> None:
        self.state.preferences.cycle_enabled = enabled
        self.repository.save(self.state)
        self.logger.info("camera cycling enabled=%s", enabled)
        self._sync_cycle_timer()

    def change_cycle_interval(self) -> None:
        dialog = CycleIntervalDialog(self, self.state.preferences.cycle_interval_seconds)
        if dialog.exec() != CycleIntervalDialog.DialogCode.Accepted:
            return
        self.state.preferences.cycle_interval_seconds = dialog.spin.value()
        self.repository.save(self.state)
        self.logger.info("cycle interval changed seconds=%d", dialog.spin.value())
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
        if self.viewer.save_current_frame(path):
            self.logger.info("camera screenshot saved id=%s", camera.id)
        else:
            QMessageBox.warning(
                self,
                "Screenshot unavailable",
                "PrintWatch has not received a camera frame yet.",
            )

    def export_diagnostics_bundle(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suggested = Path.home() / f"PrintWatch-Diagnostics-{timestamp}.zip"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export redacted diagnostics",
            str(suggested),
            "ZIP archive (*.zip)",
        )
        if not path:
            return
        try:
            destination = export_diagnostics(
                Path(path),
                state=self.state,
                app_version=__version__,
                log_path=self.log_path,
            )
        except OSError as error:
            self.logger.exception("diagnostics export failed")
            QMessageBox.warning(self, "Diagnostics export failed", str(error))
            return
        self.logger.info("redacted diagnostics exported")
        QMessageBox.information(
            self,
            "Diagnostics exported",
            "A redacted diagnostics bundle was created. Review its contents before sharing.\n\n"
            f"{destination}",
        )

    def show_onboarding_if_needed(self) -> None:
        if self.state.preferences.onboarding_completed or self.state.cameras:
            return
        box = QMessageBox(self)
        box.setWindowTitle("Welcome to PrintWatch Desktop")
        box.setIcon(QMessageBox.Icon.Information)
        box.setText(
            "<h2>Monitor all your printer cameras in one place</h2>"
            "<p>Add your FDM and resin printer streams, switch manually, or cycle between "
            "them automatically.</p>"
            "<p>PrintWatch stays local: no account, cloud service, or telemetry is required.</p>"
        )
        add_button = box.addButton("Add first camera", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        self.state.preferences.onboarding_completed = True
        self.repository.save(self.state)
        if box.clickedButton() is add_button:
            self.add_camera()

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
        self.probe.cancel()
        self.viewer.stop()
        self.window_settings.setValue("geometry", self.saveGeometry())
        self.repository.save(self.state)
        self.logger.info("application window closed")
        super().closeEvent(event)


def main() -> int:
    log_path = configure_logging()
    logger = get_logger("startup")
    logger.info("application starting version=%s", __version__)

    QApplication.setOrganizationName("Monty Labs")
    QApplication.setApplicationName("PrintWatch Desktop")
    QApplication.setApplicationVersion(__version__)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    window = PrintWatchWindow(log_path=log_path)
    window.show()
    exit_code = app.exec()
    logger.info("application exiting code=%d", exit_code)
    return exit_code
