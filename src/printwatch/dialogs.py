from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from printwatch.models import CameraKind, CameraProfile, ValidationError


class CameraDialog(QDialog):
    def __init__(self, parent=None, profile: CameraProfile | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit camera" if profile else "Add camera")
        self.setMinimumWidth(520)
        self._profile = profile

        self.name_edit = QLineEdit(profile.name if profile else "")
        self.kind_combo = QComboBox()
        self.kind_combo.addItem("ELEGOO MJPEG (port 3031)", CameraKind.ELEGOO_MJPEG)
        self.kind_combo.addItem("Custom HTTP/MJPEG stream", CameraKind.CUSTOM_HTTP)
        self.url_edit = QLineEdit(profile.url if profile else "")
        self.url_edit.setPlaceholderText("http://192.168.1.50:3031/video")
        self.notes_edit = QPlainTextEdit(profile.notes if profile else "")
        self.notes_edit.setMaximumHeight(90)

        if profile:
            index = self.kind_combo.findData(profile.kind)
            self.kind_combo.setCurrentIndex(max(index, 0))

        form = QFormLayout()
        form.addRow("Name", self.name_edit)
        form.addRow("Connection type", self.kind_combo)
        form.addRow("Stream URL", self.url_edit)
        form.addRow("Notes", self.notes_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _validate_and_accept(self) -> None:
        try:
            self.profile().validate()
        except ValidationError as error:
            QMessageBox.warning(self, "Invalid camera", str(error))
            return
        if not QUrl(self.url_edit.text().strip()).isValid():
            QMessageBox.warning(self, "Invalid camera", "The stream URL is not valid.")
            return
        self.accept()

    def profile(self) -> CameraProfile:
        return CameraProfile(
            id=self._profile.id if self._profile else str(uuid4()),
            name=self.name_edit.text(),
            url=self.url_edit.text(),
            kind=self.kind_combo.currentData(),
            enabled=self._profile.enabled if self._profile else True,
            notes=self.notes_edit.toPlainText(),
        )


class CameraManagerDialog(QDialog):
    def __init__(self, cameras: list[CameraProfile], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Manage cameras")
        self.setMinimumSize(520, 380)
        self._profiles = deepcopy(cameras)

        intro = QLabel(
            "Check the cameras that should appear in the sidebar. Drag or use the buttons "
            "to control the order used by camera cycling."
        )
        intro.setWordWrap(True)

        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.currentRowChanged.connect(self._update_button_state)
        for profile in self._profiles:
            item = QListWidgetItem(profile.name)
            item.setData(Qt.ItemDataRole.UserRole, profile.id)
            item.setFlags(
                item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsDragEnabled
            )
            item.setCheckState(
                Qt.CheckState.Checked if profile.enabled else Qt.CheckState.Unchecked
            )
            self.list_widget.addItem(item)

        self.up_button = QPushButton("Move up")
        self.up_button.clicked.connect(lambda: self._move_current(-1))
        self.down_button = QPushButton("Move down")
        self.down_button.clicked.connect(lambda: self._move_current(1))

        controls = QHBoxLayout()
        controls.addWidget(self.up_button)
        controls.addWidget(self.down_button)
        controls.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addWidget(self.list_widget)
        layout.addLayout(controls)
        layout.addWidget(buttons)

        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)
        self._update_button_state()

    def _move_current(self, offset: int) -> None:
        current = self.list_widget.currentRow()
        destination = current + offset
        if current < 0 or destination < 0 or destination >= self.list_widget.count():
            return
        item = self.list_widget.takeItem(current)
        self.list_widget.insertItem(destination, item)
        self.list_widget.setCurrentRow(destination)

    def _update_button_state(self) -> None:
        row = self.list_widget.currentRow()
        self.up_button.setEnabled(row > 0)
        self.down_button.setEnabled(0 <= row < self.list_widget.count() - 1)

    def profiles(self) -> list[CameraProfile]:
        by_id = {profile.id: profile for profile in self._profiles}
        ordered: list[CameraProfile] = []
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            profile = by_id[item.data(Qt.ItemDataRole.UserRole)]
            profile.enabled = item.checkState() == Qt.CheckState.Checked
            ordered.append(profile)
        return ordered


class CycleIntervalDialog(QDialog):
    def __init__(self, parent=None, current_seconds: int = 15) -> None:
        super().__init__(parent)
        self.setWindowTitle("Camera cycle interval")
        self.spin = QSpinBox()
        self.spin.setRange(5, 3600)
        self.spin.setSuffix(" seconds")
        self.spin.setValue(current_seconds)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        form = QFormLayout()
        form.addRow("Switch cameras every", self.spin)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)
