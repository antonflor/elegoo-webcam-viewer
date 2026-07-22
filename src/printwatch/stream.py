from __future__ import annotations

from collections.abc import Iterable
from contextlib import suppress

from PyQt6.QtCore import QSize, Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QPixmap, QResizeEvent
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class MjpegFrameParser:
    """Extract JPEG frames from an MJPEG byte stream without parsing vendor headers."""

    start_marker = b"\xff\xd8"
    end_marker = b"\xff\xd9"

    def __init__(self, max_buffer_bytes: int = 16 * 1024 * 1024) -> None:
        self.max_buffer_bytes = max_buffer_bytes
        self._buffer = bytearray()

    def reset(self) -> None:
        self._buffer.clear()

    def feed(self, data: bytes | bytearray | memoryview) -> list[bytes]:
        if data:
            self._buffer.extend(data)

        frames: list[bytes] = []
        while True:
            start = self._buffer.find(self.start_marker)
            if start < 0:
                self._trim_without_frame_start()
                break

            if start:
                del self._buffer[:start]

            end = self._buffer.find(self.end_marker, len(self.start_marker))
            if end < 0:
                self._trim_oversized_frame()
                break

            end += len(self.end_marker)
            frames.append(bytes(self._buffer[:end]))
            del self._buffer[:end]

        return frames

    def _trim_without_frame_start(self) -> None:
        if len(self._buffer) <= self.max_buffer_bytes:
            return
        trailing = self._buffer[-1:] if self._buffer.endswith(b"\xff") else b""
        self._buffer.clear()
        self._buffer.extend(trailing)

    def _trim_oversized_frame(self) -> None:
        if len(self._buffer) > self.max_buffer_bytes:
            self._buffer.clear()


class MjpegViewer(QWidget):
    """A lightweight Qt Network viewer for direct MJPEG or JPEG endpoints."""

    status_changed = pyqtSignal(str)
    frame_received = pyqtSignal(QSize)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._manager = QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None
        self._parser = MjpegFrameParser()
        self._source_pixmap = QPixmap()
        self._url = ""
        self._stopping = False
        self._received_frame = False
        self._retry_attempt = 0

        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setSingleShot(True)
        self._reconnect_timer.timeout.connect(self.reload)

        self._image_label = QLabel("Waiting for a camera stream…")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(320, 240)
        self._image_label.setStyleSheet("background: #111; color: #ddd; padding: 16px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._image_label)

    @property
    def has_frame(self) -> bool:
        return not self._source_pixmap.isNull()

    @property
    def current_url(self) -> str:
        return self._url

    def start(self, url: str) -> None:
        self.stop(clear_frame=False)
        self._url = url.strip()
        self._parser.reset()
        self._received_frame = False
        self._stopping = False
        self._image_label.setText("Connecting to camera…")
        self.status_changed.emit("Connecting to camera…")

        request = QNetworkRequest(QUrl(self._url))
        request.setRawHeader(
            b"Accept",
            b"multipart/x-mixed-replace,image/jpeg,*/*;q=0.5",
        )
        request.setRawHeader(b"User-Agent", b"PrintWatch-Desktop/0.2")
        request.setAttribute(
            QNetworkRequest.Attribute.CacheLoadControlAttribute,
            QNetworkRequest.CacheLoadControl.AlwaysNetwork,
        )
        request.setTransferTimeout(15_000)

        reply = self._manager.get(request)
        self._reply = reply
        reply.readyRead.connect(self._read_available_data)
        reply.errorOccurred.connect(self._network_error)
        reply.finished.connect(self._reply_finished)

    def reload(self) -> None:
        if self._url:
            self.start(self._url)

    def stop(self, *, clear_frame: bool = False) -> None:
        self._stopping = True
        self._reconnect_timer.stop()
        if self._reply is not None:
            reply = self._reply
            self._reply = None
            self._disconnect_reply(reply)
            reply.abort()
            reply.deleteLater()
        self._parser.reset()
        self._received_frame = False
        if clear_frame:
            self._source_pixmap = QPixmap()
            self._image_label.clear()
            self._image_label.setText("Waiting for a camera stream…")

    def save_current_frame(self, path: str) -> bool:
        if self._source_pixmap.isNull():
            return False
        return self._source_pixmap.save(path)

    def _disconnect_reply(self, reply: QNetworkReply) -> None:
        for signal, slot in (
            (reply.readyRead, self._read_available_data),
            (reply.errorOccurred, self._network_error),
            (reply.finished, self._reply_finished),
        ):
            with suppress(TypeError, RuntimeError):
                signal.disconnect(slot)

    def _current_sender_reply(self) -> QNetworkReply | None:
        sender = self.sender()
        if isinstance(sender, QNetworkReply) and sender is self._reply:
            return sender
        return None

    def _read_available_data(self) -> None:
        reply = self._current_sender_reply()
        if reply is None:
            return
        frames = self._parser.feed(bytes(reply.readAll()))
        self._display_frames(frames)

    def _display_frames(self, frames: Iterable[bytes]) -> None:
        newest_pixmap: QPixmap | None = None
        for frame in frames:
            pixmap = QPixmap()
            if pixmap.loadFromData(frame):
                newest_pixmap = pixmap

        if newest_pixmap is None:
            return

        self._source_pixmap = newest_pixmap
        self._received_frame = True
        self._retry_attempt = 0
        self._render_scaled_frame()
        self.status_changed.emit(f"Live — {newest_pixmap.width()}×{newest_pixmap.height()}")
        self.frame_received.emit(newest_pixmap.size())

    def _network_error(self, error: QNetworkReply.NetworkError) -> None:
        reply = self._current_sender_reply()
        if (
            reply is None
            or self._stopping
            or error == QNetworkReply.NetworkError.OperationCanceledError
        ):
            return
        self.status_changed.emit(f"Camera connection failed: {reply.errorString()}")
        if not self.has_frame:
            self._image_label.setText(
                "Could not reach this camera.\n\n"
                "Verify the stream URL and that this device is on the same network."
            )

    def _reply_finished(self) -> None:
        reply = self._current_sender_reply()
        if reply is None:
            return
        self._reply = None
        self._disconnect_reply(reply)
        reply.deleteLater()
        if self._stopping or not self._url:
            return

        # A single JPEG endpoint is refreshed quickly; a failed/ended MJPEG stream backs off.
        if self._received_frame:
            delay_ms = 1_000
        else:
            self._retry_attempt = min(self._retry_attempt + 1, 6)
            delay_ms = min(30_000, 2_000 * (2 ** (self._retry_attempt - 1)))
        self.status_changed.emit(f"Reconnecting in {delay_ms // 1000}s…")
        self._reconnect_timer.start(delay_ms)

    def _render_scaled_frame(self) -> None:
        if self._source_pixmap.isNull():
            return
        scaled = self._source_pixmap.scaled(
            self._image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        self._render_scaled_frame()
        super().resizeEvent(event)
