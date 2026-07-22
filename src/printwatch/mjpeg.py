from __future__ import annotations


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
