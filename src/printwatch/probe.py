from __future__ import annotations

from contextlib import suppress

from PyQt6.QtCore import QElapsedTimer, QObject, QTimer, QUrl, pyqtSignal
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from printwatch.mjpeg import MjpegFrameParser


class CameraProbe(QObject):
    """Test a camera URL by waiting for one valid JPEG frame."""

    completed = pyqtSignal(bool, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._manager = QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None
        self._parser = MjpegFrameParser(max_buffer_bytes=4 * 1024 * 1024)
        self._elapsed = QElapsedTimer()
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.timeout.connect(self._timed_out)
        self._finished = False
        self._timeout_ms = 10_000

    def start(self, url: str, timeout_ms: int = 10_000) -> None:
        self.cancel()
        self._finished = False
        self._parser.reset()
        self._elapsed.start()
        self._timeout_ms = max(1_000, timeout_ms)

        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(
            b"Accept",
            b"multipart/x-mixed-replace,image/jpeg,*/*;q=0.5",
        )
        request.setRawHeader(b"User-Agent", b"PrintWatch-Desktop/0.2")
        request.setAttribute(
            QNetworkRequest.Attribute.CacheLoadControlAttribute,
            QNetworkRequest.CacheLoadControl.AlwaysNetwork,
        )
        request.setTransferTimeout(self._timeout_ms)

        reply = self._manager.get(request)
        self._reply = reply
        reply.readyRead.connect(self._read_available_data)
        reply.errorOccurred.connect(self._network_error)
        reply.finished.connect(self._reply_finished)
        self._timeout.start(self._timeout_ms)

    def cancel(self) -> None:
        self._timeout.stop()
        if self._reply is not None:
            reply = self._reply
            self._reply = None
            self._disconnect_reply(reply)
            reply.abort()
            reply.deleteLater()

    def _disconnect_reply(self, reply: QNetworkReply) -> None:
        for signal, slot in (
            (reply.readyRead, self._read_available_data),
            (reply.errorOccurred, self._network_error),
            (reply.finished, self._reply_finished),
        ):
            with suppress(TypeError, RuntimeError):
                signal.disconnect(slot)

    def _current_reply(self) -> QNetworkReply | None:
        sender = self.sender()
        if isinstance(sender, QNetworkReply) and sender is self._reply:
            return sender
        return None

    def _read_available_data(self) -> None:
        reply = self._current_reply()
        if reply is None:
            return
        if self._parser.feed(bytes(reply.readAll())):
            elapsed_ms = self._elapsed.elapsed()
            self._complete(True, f"Received a valid camera frame in {elapsed_ms} ms.")

    def _network_error(self, error: QNetworkReply.NetworkError) -> None:
        if error == QNetworkReply.NetworkError.OperationCanceledError:
            return
        self._complete(False, "The camera connection failed before a valid frame was received.")

    def _reply_finished(self) -> None:
        if self._finished:
            return
        self._complete(False, "The endpoint closed without returning a valid JPEG frame.")

    def _timed_out(self) -> None:
        timeout_seconds = self._timeout_ms / 1000
        self._complete(
            False,
            f"The camera did not return a valid frame within {timeout_seconds:g} seconds.",
        )

    def _complete(self, success: bool, message: str) -> None:
        if self._finished:
            return
        self._finished = True
        self._timeout.stop()
        if self._reply is not None:
            reply = self._reply
            self._reply = None
            self._disconnect_reply(reply)
            reply.abort()
            reply.deleteLater()
        self.completed.emit(success, message)
