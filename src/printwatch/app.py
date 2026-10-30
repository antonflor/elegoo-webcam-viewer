from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSettings, QStandardPaths, Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
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
from printwatch.models import CameraKind, CameraProfile
from printwatch.probe import CameraProbe
from printwatch.storage import StateRepository
from printwatch.stream import MjpegViewer
from printwatch.theme import (
    STATE_LABELS,
    StreamState,
    app_icon,
    apply_theme,
    pill_style,
    state_dot,
)

KIND_LABELS = {
    CameraKind.ELEGOO_MJPEG: "ELEGOO MJPEG",
    CameraKind.CUSTOM_HTTP: "HTTP stream",
}


class CameraHeader(QWidget):
    """Title bar above the stream: camera name, connection state, and stream details."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CameraHeader")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.title = QLabel()
        self.title.setObjectName("CameraTitle")
        self.pill = QLabel()
        self.pill.setObjectName("StatePill")
        self.meta = QLabel()
        self.meta.setObjectName("CameraMeta")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(10)
        layout.addWidget(self.title)
        layout.addWidget(self.pill)
        layout.addStretch(1)
        layout.addWidget(self.meta)
        self.set_state(StreamState.IDLE)

    def set_state(self, state: StreamState) -> None:
        self.pill.setText(f"●  {STATE_LABELS[state].upper()}")
        self.pill.setStyleSheet(pill_style(state))


class EmptyState(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("EmptyState")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        icon = QLabel()
        icon.setPixmap(app_icon().pixmap(88, 88))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title = QLabel()
        self.title.setObjectName("EmptyTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body = QLabel()
        self.body.setObjectName("EmptyBody")
        self.body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body.setWordWrap(True)
        self.button = QPushButton()
        self.button.setObjectName("PrimaryButton")
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self.button)
        button_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addStretch(1)
        layout.addWidget(icon)
        layout.addSpacing(8)
        layout.addWidget(self.title)
        layout.addWidget(self.body)
        layout.addSpacing(12)
        layout.addLayout(button_row)
        layout.addStretch(1)

    def show_message(self, title: str, body: str, button: str) -> None:
        self.title.setText(title)
        self.body.setText(body)
        self.button.setText(button)


class PrintWatchWindow(QMainWindow):
    def __init__(
        self,
        repository: StateRepository | None = None,
        log_path: Path | None = None,
        settings: QSettings | None = None,
    ) -> None:
        super().__init__()
        self.repository = repository or StateRepository()
        self.state = self.repository.load()
        self.log_path = log_path
        self.logger = get_logger("app")
        self.window_settings = settings or QSettings("Monty Labs", "PrintWatch Desktop")
        self._probe_camera_id: str | None = None
        self._probe_camera_name = "Camera"

        self.setWindowTitle("PrintWatch Desktop")
        self.setWindowIcon(app_icon())
        self.setMinimumSize(820, 520)
        self.resize(1180, 720)
        geometry = self.window_settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        self.camera_list = QListWidget()
        self.camera_list.setObjectName("CameraList")
        self.camera_list.setMinimumWidth(200)
        self.camera_list.currentItemChanged.connect(self._camera_selection_changed)

        self.sidebar_title = QLabel()
        self.sidebar_title.setObjectName("SidebarTitle")
        add_button = QPushButton("+  Add camera")
        add_button.setObjectName("SidebarAdd")
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.clicked.connect(self.add_camera)

        self.empty_state = EmptyState()
        self.empty_state.button.clicked.connect(self._empty_state_action)

        self.viewer = MjpegViewer()
        self.viewer.status_changed.connect(self._viewer_status_changed)
        self.viewer.state_changed.connect(self._viewer_state_changed)
        self.viewer.frame_received.connect(lambda _size: self.screenshot_action.setEnabled(True))

        self.header = CameraHeader()
        viewer_page = QWidget()
        viewer_layout = QVBoxLayout(viewer_page)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(0)
        viewer_layout.addWidget(self.header)
        viewer_layout.addWidget(self.viewer, 1)

        self.probe = CameraProbe(self)
        self.probe.completed.connect(self._probe_completed)

        self.viewer_stack = QStackedWidget()
        self.viewer_stack.addWidget(self.empty_state)
        self.viewer_stack.addWidget(viewer_page)
        self._viewer_page = viewer_page

        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 14, 10, 10)
        sidebar_layout.setSpacing(8)
        sidebar_layout.addWidget(self.sidebar_title)
        sidebar_layout.addWidget(self.camera_list, 1)
        sidebar_layout.addWidget(add_button)

        splitter = QSplitter()
        splitter.setHandleWidth(1)
        splitter.addWidget(sidebar)
        splitter.addWidget(self.viewer_stack)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([230, 950])
        self.setCentralWidget(splitter)

        self._build_toolbar()
        self.cycle_timer = QTimer(self)
        self.cycle_timer.timeout.connect(self.select_next_camera)
        self.meta_timer = QTimer(self)
        self.meta_timer.timeout.connect(self._update_header_meta)
        self.meta_timer.start(1_000)

        self._refresh_camera_list()
        self._restore_selection()
        self._sync_cycle_timer()
        if not self.state.cameras:
            self.statusBar().showMessage("Ready — no account, cloud, or telemetry")
        self.logger.info(
            "window initialized cameras=%d enabled=%d",
            len(self.state.cameras),
            sum(camera.enabled for camera in self.state.cameras),
        )
        QTimer.singleShot(0, self.show_onboarding_if_needed)

    def _action(self, text: str, slot, shortcut=None, tip: str = "") -> QAction:
        action = QAction(text, self)
        if shortcut is not None:
            action.setShortcut(
                shortcut if isinstance(shortcut, QKeySequence) else QKeySequence(shortcut)
            )
        hint = action.shortcut().toString(QKeySequence.SequenceFormat.NativeText)
        action.setToolTip(f"{tip} ({hint})" if tip and hint else tip or text)
        action.triggered.connect(slot)
        return action

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(toolbar)

        self.add_action = self._action(
            "Add", self.add_camera, QKeySequence.StandardKey.New, "Add a camera"
        )
        self.edit_action = self._action(
            "Edit", self.edit_camera, "Ctrl+E", "Edit the selected camera"
        )
        self.remove_action = self._action(
            "Remove", self.remove_camera, QKeySequence.StandardKey.Delete, "Remove the camera"
        )
        self.manage_action = self._action(
            "Manage", self.manage_cameras, "Ctrl+M", "Enable, disable, and reorder cameras"
        )
        for action in (self.add_action, self.edit_action, self.remove_action, self.manage_action):
            toolbar.addAction(action)
        toolbar.addSeparator()

        self.test_action = self._action(
            "Test", self.test_camera, "Ctrl+T", "Check that the camera returns a frame"
        )
        self.reload_action = self._action(
            "Reconnect", self.viewer.reload, QKeySequence.StandardKey.Refresh, "Reconnect"
        )
        self.screenshot_action = self._action(
            "Screenshot", self.take_screenshot, "Ctrl+Shift+S", "Save the current frame"
        )
        self.screenshot_action.setEnabled(False)
        self.pin_action = self._action(
            "Pin to top", lambda: None, "Ctrl+Shift+T", "Keep this window above others"
        )
        self.pin_action.setCheckable(True)
        self.pin_action.toggled.connect(self.toggle_always_on_top)
        for action in (
            self.test_action,
            self.reload_action,
            self.screenshot_action,
            self.pin_action,
        ):
            toolbar.addAction(action)
        toolbar.addSeparator()

        self.cycle_action = self._action(
            "Cycle cameras", lambda: None, "Ctrl+L", "Switch cameras automatically"
        )
        self.cycle_action.setCheckable(True)
        self.cycle_action.setChecked(self.state.preferences.cycle_enabled)
        self.cycle_action.toggled.connect(self.toggle_cycle)
        toolbar.addAction(self.cycle_action)

        self.cycle_interval_action = self._action(
            f"Every {self.state.preferences.cycle_interval_seconds}s",
            self.change_cycle_interval,
            tip="Change how often cameras switch",
        )
        toolbar.addAction(self.cycle_interval_action)

        next_action = self._action("Next camera", self.select_next_camera, "Ctrl+Tab")
        previous_action = self._action(
            "Previous camera", self.select_previous_camera, "Ctrl+Shift+Tab"
        )
        self.addActions([next_action, previous_action])

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        toolbar.addAction(
            self._action(
                "Diagnostics",
                self.export_diagnostics_bundle,
                tip="Export a redacted troubleshooting bundle",
            )
        )
        toolbar.addAction(self._action("About", self.show_about))

    def _refresh_camera_list(self) -> None:
        selected_id = self.state.preferences.selected_camera_id
        self.camera_list.blockSignals(True)
        self.camera_list.clear()
        self.camera_list.blockSignals(False)
        for camera in self.state.cameras:
            if not camera.enabled:
                continue
            item = QListWidgetItem(state_dot(StreamState.IDLE), camera.name)
            item.setData(Qt.ItemDataRole.UserRole, camera.id)
            item.setToolTip(f"{KIND_LABELS[camera.kind]} · {camera.url}")
            self.camera_list.addItem(item)
            if camera.id == selected_id:
                self.camera_list.setCurrentItem(item)

        enabled_count = self.camera_list.count()
        self.sidebar_title.setText(f"CAMERAS  ·  {enabled_count}")
        if enabled_count:
            self.viewer_stack.setCurrentWidget(self._viewer_page)
        else:
            if self.state.cameras:
                self.empty_state.show_message(
                    "No cameras are enabled",
                    "Turn cameras on and set their cycle order in Manage.",
                    "Manage cameras",
                )
            else:
                self.empty_state.show_message(
                    "Watch every printer from one window",
                    "Add an ELEGOO printer camera or any direct HTTP MJPEG/JPEG stream.\n"
                    "Everything stays on your local network.",
                    "Add your first camera",
                )
            self.viewer.stop(clear_frame=True)
            self.viewer_stack.setCurrentWidget(self.empty_state)
            self.setWindowTitle("PrintWatch Desktop")
        self._set_camera_actions_enabled(enabled_count > 0)

    def _empty_state_action(self) -> None:
        if self.state.cameras:
            self.manage_cameras()
        else:
            self.add_camera()

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

    def _camera_selection_changed(
        self, current: QListWidgetItem | None, previous: QListWidgetItem | None
    ) -> None:
        if previous is not None:
            previous.setIcon(state_dot(StreamState.IDLE))
        if current is None:
            return
        camera_id = current.data(Qt.ItemDataRole.UserRole)
        camera = next((item for item in self.state.cameras if item.id == camera_id), None)
        if camera is None:
            return
        self.state.preferences.selected_camera_id = camera.id
        self.repository.save(self.state)
        self.viewer_stack.setCurrentWidget(self._viewer_page)
        self.screenshot_action.setEnabled(False)
        self.header.title.setText(camera.name)
        self.viewer.start(camera.url)
        self._update_header_meta()
        self.setWindowTitle(f"{camera.name} — PrintWatch Desktop")
        self.logger.info("camera selected id=%s kind=%s", camera.id, camera.kind.value)

    def _viewer_status_changed(self, status: str) -> None:
        self.statusBar().showMessage(status)

    def _viewer_state_changed(self, value: str) -> None:
        state = StreamState(value)
        self.header.set_state(state)
        item = self.camera_list.currentItem()
        if item is not None:
            item.setIcon(state_dot(state))
        self._update_header_meta()

    def _update_header_meta(self) -> None:
        camera = self.current_camera()
        if camera is None:
            self.header.meta.setText("")
            return
        parts = [KIND_LABELS[camera.kind]]
        if self.viewer.state == StreamState.LIVE:
            size = self.viewer.frame_size
            parts.append(f"{size.width()}x{size.height()}")
            if self.viewer.fps:
                parts.append(f"{self.viewer.fps:.0f} fps")
        if self.cycle_timer.isActive():
            parts.append(f"cycling every {self.state.preferences.cycle_interval_seconds}s")
        self.header.meta.setText("   ·   ".join(parts))

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
        # Rebuilding the list reselects the camera, which restarts its stream once.
        self._refresh_camera_list()
        self._restore_selection()

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
        self._step_camera(1)

    def select_previous_camera(self) -> None:
        self._step_camera(-1)

    def _step_camera(self, offset: int) -> None:
        count = self.camera_list.count()
        if count < 2:
            return
        self.camera_list.setCurrentRow((self.camera_list.currentRow() + offset) % count)
        if self.cycle_timer.isActive():
            # A manual switch restarts the countdown so the chosen camera gets a full interval.
            self.cycle_timer.start()

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
        self._update_header_meta()

    def toggle_always_on_top(self, enabled: bool) -> None:
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        self.show()

    def take_screenshot(self) -> None:
        camera = self.current_camera()
        if camera is None:
            return
        pictures = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)
        folder = Path(pictures) if pictures and Path(pictures).exists() else Path.home()
        safe_name = "".join(character if character.isalnum() else "_" for character in camera.name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suggested = folder / f"{safe_name}_{timestamp}.png"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save camera screenshot", str(suggested), "PNG image (*.png);;JPEG image (*.jpg)"
        )
        if not path:
            return
        if self.viewer.save_current_frame(path):
            self.logger.info("camera screenshot saved id=%s", camera.id)
            self.statusBar().showMessage(f"Screenshot saved to {path}", 5_000)
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
        box.setIconPixmap(app_icon().pixmap(64, 64))
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
        box = QMessageBox(self)
        box.setWindowTitle("About PrintWatch Desktop")
        box.setIconPixmap(app_icon().pixmap(64, 64))
        box.setText(
            f"<h2>PrintWatch Desktop {__version__}</h2>"
            "<p>A local-first, multi-camera monitor for 3D printers.</p>"
            "<p>No account, cloud service, or telemetry is required.</p>"
            '<p><a href="https://github.com/antonflor/elegoo-webcam-viewer">'
            "github.com/antonflor/elegoo-webcam-viewer</a> · MIT License · "
            "Built with Qt for Python (PySide6, LGPLv3).</p>"
            "<p><b>Independent project:</b> not affiliated with or endorsed by ELEGOO. "
            "ELEGOO and Matrix are trademarks of their respective owners.</p>"
            "<p>This application is a monitoring convenience, not a printer safety system.</p>"
        )
        box.setTextFormat(Qt.TextFormat.RichText)
        box.exec()

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
    apply_theme(app)
    app.setQuitOnLastWindowClosed(True)
    window = PrintWatchWindow(log_path=log_path)
    window.show()
    exit_code = app.exec()
    logger.info("application exiting code=%d", exit_code)
    return exit_code
