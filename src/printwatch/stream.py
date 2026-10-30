from __future__ import annotations

from collections.abc import Iterable
from contextlib import suppress

from PySide6.QtCore import QElapsedTimer, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QPixmap, QResizeEvent
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from printwatch.mjpeg import USER_AGENT, MjpegFrameParser
from printwatch.theme import StreamState


class MjpegViewer(QWidget):
    """A lightweight Qt Network viewer for direct MJPEG or JPEG endpoints."""

    status_changed = Signal(str)
    frame_received = Signal(QSize)
    state_changed = Signal(str)

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
        self._state = StreamState.IDLE
        self._fps = 0.0
        self._fps_frames = 0
        self._fps_clock = QElapsedTimer()

        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setSingleShot(True)
        self._reconnect_timer.timeout.connect(self.reload)

        self._image_label = QLabel("Waiting for a camera stream…")
        self._image_label.setObjectName("ViewerSurface")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setWordWrap(True)
        self._image_label.setMinimumSize(320, 240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._image_label)

    @property
    def has_frame(self) -> bool:
        return not self._source_pixmap.isNull()

    @property
    def current_url(self) -> str:
        return self._url

    @property
    def state(self) -> StreamState:
        return self._state

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def frame_size(self) -> QSize:
        return self._source_pixmap.size()

    def start(self, url: str, *, keep_frame: bool = False) -> None:
        """Connect to ``url``.

        The last frame is kept only when reconnecting to the same camera, so switching to an
        unreachable camera never keeps showing the previous camera's picture.
        """
        url = url.strip()
        same_camera = keep_frame and url == self._url
        self.stop(clear_frame=not same_camera)
        if not same_camera:
            self._retry_attempt = 0
        self._url = url
        self._parser.reset()
        self._received_frame = False
        self._stopping = False
        self._fps = 0.0
        self._fps_frames = 0
        self._fps_clock.start()
        if self.has_frame:
            self._set_state(StreamState.RECONNECTING)
            self.status_changed.emit("Reconnecting to camera…")
        elif self._retry_attempt:
            # Background retry of an unreachable camera: stay "Offline" instead of flickering.
            self.status_changed.emit("Camera offline — retrying…")
        else:
            self._image_label.setText("Connecting to camera…")
            self._set_state(StreamState.CONNECTING)
            self.status_changed.emit("Connecting to camera…")

        request = QNetworkRequest(QUrl(self._url))
        request.setRawHeader(
            b"Accept",
            b"multipart/x-mixed-replace,image/jpeg,*/*;q=0.5",
        )
        request.setRawHeader(b"User-Agent", USER_AGENT)
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
            self.start(self._url, keep_frame=True)

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
            self._set_state(StreamState.IDLE)

    def save_current_frame(self, path: str) -> bool:
        if self._source_pixmap.isNull():
            return False
        return self._source_pixmap.save(path)

    def _set_state(self, state: StreamState) -> None:
        if state != self._state:
            self._state = state
            self.state_changed.emit(state.value)

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
                self._count_frame()

        if newest_pixmap is None:
            return

        self._source_pixmap = newest_pixmap
        self._received_frame = True
        self._retry_attempt = 0
        self._render_scaled_frame()
        self._set_state(StreamState.LIVE)
        self.status_changed.emit(f"Live — {newest_pixmap.width()}x{newest_pixmap.height()}")
        self.frame_received.emit(newest_pixmap.size())

    def _count_frame(self) -> None:
        self._fps_frames += 1
        elapsed = self._fps_clock.elapsed()
        if elapsed >= 1_000:
            self._fps = self._fps_frames * 1000 / elapsed
            self._fps_frames = 0
            self._fps_clock.restart()

    def _network_error(self, error: QNetworkReply.NetworkError) -> None:
        reply = self._current_sender_reply()
        if (
            reply is None
            or self._stopping
            or error == QNetworkReply.NetworkError.OperationCanceledError
        ):
            return
        self.status_changed.emit(f"Camera connection failed: {reply.errorString()}")
        self._set_state(StreamState.OFFLINE)
        if not self.has_frame:
            self._image_label.setText(
                "Could not reach this camera.\n\n"
                "Check that the printer is on, the stream URL is correct, and this computer "
                "is on the same network. PrintWatch will keep retrying."
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
            self._set_state(StreamState.OFFLINE)
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
