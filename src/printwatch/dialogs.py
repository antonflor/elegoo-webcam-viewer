from __future__ import annotations

from uuid import uuid4

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
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
            enabled=True,
            notes=self.notes_edit.toPlainText(),
        )


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
